FROM python:3.11.7
ARG DB_URL
ENV DB_URL=$DB_URL
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install psycopg2-binary
COPY ./logreef /code/logreef
CMD ["uvicorn", "logreef.main:app", "--host", "0.0.0.0", "--port", "80"]