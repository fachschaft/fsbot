FROM python:3.7-alpine

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

WORKDIR /bot/

CMD python3 main.py
