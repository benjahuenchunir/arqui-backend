# ./django-docker/app/Dockerfile
FROM python:3.11

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/opt:/opt/db2

# install dependencies
COPY jobs_master/requirements/common.txt . 
COPY jobs_master/requirements/production.txt . 
RUN pip install --upgrade --no-cache-dir -r production.txt

# copy project
WORKDIR /opt
COPY db /opt/db
COPY jobs_master /opt/