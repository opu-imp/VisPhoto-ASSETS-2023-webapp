FROM python:3.6-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-dev \
    libmecab-dev \
    mecab \
    mecab-ipadic \
    mecab-ipadic-utf8

RUN curl https://rclone.org/install.sh | bash

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

WORKDIR /code
