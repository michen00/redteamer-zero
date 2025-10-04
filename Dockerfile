# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -e .[dev]

CMD ["pytest", "-q"]
