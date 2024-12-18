from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from logreef.persistence import models
from logreef.persistence.database import add_to_db


def create(
    db: Session,
    user_id: int,
    name: str,
    started_on: datetime | None = None,
    description: str | None = None,
    capacity_value: float | None = None,
    capacity_units: str | None = None,
) -> models.Aquarium:
    now = datetime.now(timezone.utc)
    db_aquarium = models.Aquarium(
        user_id=user_id,
        name=name,
        started_on=started_on,
        created_on=now,
        updated_on=now,
        description=description,
        capacity_value=capacity_value,
        capacity_units=capacity_units,
    )
    add_to_db(db, db_aquarium)
    return db_aquarium


def get_by_name(db: Session, user_id: int, name: str):
    return (
        db.query(models.Aquarium)
        .filter(models.Aquarium.user_id == user_id)
        .filter(models.Aquarium.name == name)
        .first()
    )


def get_by_user(db: Session, user_id: int) -> list[models.Aquarium]:
    result = db.execute(
        select(models.Aquarium).where(models.Aquarium.user_id == user_id)
    )
    return [row[0] for row in result]


def get_all(db: Session, user_id: int) -> list[models.Aquarium]:
    return db.query(models.Aquarium).filter(models.Aquarium.user_id == user_id).all()


def update_by_id(
    db: Session,
    aquarium_id: int,
    user_id: int,
    description: str | None = None,
    started_on: datetime | None = None,
    capacity_value: float | None = None,
    capacity_units: str | None = None,
):
    updates = {models.Aquarium.updated_on: datetime.now(timezone.utc)}
    if description is not None:
        updates[models.Aquarium.description] = description
    if started_on is not None:
        updates[models.Aquarium.started_on] = started_on
    if capacity_value is not None:
        updates[models.Aquarium.capacity_value] = capacity_value
    if capacity_units is not None:
        updates[models.Aquarium.capacity_units] = capacity_units
    db.query(models.Aquarium).filter(models.Aquarium.user_id == user_id).filter(
        models.Aquarium.id == aquarium_id
    ).update(updates)
    db.commit()
    return True


def delete_by_id(db: Session, user_id: int, aquarium_id: int):
    rows = (
        db.query(models.Aquarium)
        .filter(models.Aquarium.user_id == user_id)
        .filter(models.Aquarium.id == aquarium_id)
        .delete()
    )
    db.commit()
    return rows
