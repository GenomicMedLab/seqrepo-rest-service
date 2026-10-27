# syntax = docker/dockerfile:experimental

# docker build -t biocommons/seqrepo-rest-service .

FROM ubuntu:22.04

RUN apt update && apt upgrade -y && apt install -y \
    curl \
    git \
    python3-pip \
    zip

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -U setuptools "pip>=26.2.2"

COPY . /app/
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -r requirements.txt && python3 -m pip install --no-deps -e .

EXPOSE 5000

CMD ["seqrepo-rest-service"]
