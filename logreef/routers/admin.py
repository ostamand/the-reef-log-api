from typing import Annotated
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from azure.storage.blob import BlobServiceClient

from logreef.persistence import users
from logreef.user import get_current_user
from logreef import schemas
from logreef.persistence.database import get_session, Session
from logreef.config import ConfigAPI, get_config
from logreef.security import create_email_confirmation_token


BLOB_CONTAINER_NAME = "thereeflog"


router = APIRouter()


def check_for_admin(user: schemas.User):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Need admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

@router.post("/update-password")
def update_password(req: schemas.UpdatePassword, current_user: Annotated[schemas.User, Depends(get_current_user)], db: Session = Depends(get_session)):
    # check that password match 
    user = users.authenticate(db, current_user.username, req.old_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, old password or account not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    ok = users.update_password(db, user.id, req.new_password)
    
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed, try again",
        )
    return {"detail": "Password changed", "username": user.username, "email": user.email}
    

@router.get("/update-demo-user")
def daily_demo_user_update(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_session),
    username: str = "demo",
):
    check_for_admin(current_user)
    query = f"""UPDATE param_values
        SET timestamp = timestamp + INTERVAL '1 day'
        FROM users
        WHERE param_values.user_id = users.id
        AND users.username = '{username}';
    """
    try:
        conn = db.connection().connection
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo user update failed",
        )
    finally:
        conn.close()
    return {
        "detail": "Updated user demo",
    }


@router.get("/backup-user")
def backup_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    username: str,
    db: Session = Depends(get_session),
):
    check_for_admin(current_user)

    query = f"""
        SELECT param_values.* FROM param_values
        JOIN users ON param_values.user_id = users.id
        WHERE users.username = '{username}'
    """

    filename = f"{username}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

    try:
        conn = db.connection().connection
        with conn.cursor() as cur:
            with open(filename, "w") as f:
                cur.copy_expert(f"COPY ({query}) TO STDOUT WITH CSV HEADER", f)

        # save to storage account
        blob_service_client = BlobServiceClient.from_connection_string(
            get_config(ConfigAPI.STORAGE_CONNECTION_STRING)
        )
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(f"params-daily-dump/{filename}")

        with open(filename, "rb") as f:
            blob_client.upload_blob(f, overwrite=True)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data backup failed",
        )
    finally:
        conn.close()
        if os.path.exists(filename):
            os.remove(filename)
    return {
        "blob_name": blob_client.blob_name,
        "url": blob_client.url,
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/confirmation-token")
def generate_confirmation_token(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    email: str,
):
    check_for_admin(current_user)
    token = create_email_confirmation_token(email)
    return {"token": token}
