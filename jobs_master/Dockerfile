# ./django-docker/app/Dockerfile
FROM python:3.11

# set work directory
WORKDIR /opt/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY ./requirements/common.txt /opt/common.txt
COPY ./requirements/production.txt /opt/production.txt
RUN pip install --upgrade --no-cache-dir -r /opt/production.txt

# copy project
COPY . /opt/