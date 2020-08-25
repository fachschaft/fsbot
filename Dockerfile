FROM python:3.7-alpine

RUN apk add --update\
    gcc \
    musl-dev \
  && apk upgrade\
  && rm /var/cache/apk/*

COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

WORKDIR /bot/

CMD python3 main.py
