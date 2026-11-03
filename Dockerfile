# syntax = docker/dockerfile:experimental

# docker build -t biocommons/seqrepo-rest-service .

FROM python:3.11-slim

RUN apt update && apt upgrade -y && apt install -y \
    curl \
    git \
    zip

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -U setuptools "pip>=26.2.2"

COPY . /app/
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -r requirements.txt && python3 -m pip install --no-deps -e .

EXPOSE 5000

CMD ["seqrepo-rest-service"]
