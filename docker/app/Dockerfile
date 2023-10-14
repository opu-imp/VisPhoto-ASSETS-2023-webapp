FROM python:3.6-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

WORKDIR /code
