# ./django-docker/app/Dockerfile
FROM python:3.11

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/opt:/opt/db2

# install dependencies
COPY jobs_master/requirements.txt . 
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# copy project
WORKDIR /opt
COPY db /opt/db
COPY jobs_master /opt/

# Instala New Relic
RUN pip install newrelic

# Copia el archivo newrelic.ini
COPY jobs_master/newrelic.ini .

# Comando predeterminado (puede ser sobrescrito por docker-compose)
CMD ["sh", "-c", "NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn producer:app --reload --host 0.0.0.0 --port 7998"]