FROM python:3.13.7-alpine3.22

LABEL maintainer="kumarswaraj"

ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

RUN apk add --no-cache build-base

COPY requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false

RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r /tmp/requirements.txt && \
  if [ "$DEV" = "true" ]; then \
  /py/bin/pip install -r /tmp/requirements.dev.txt ; \
  fi && \
  rm -rf /tmp

COPY app /app
WORKDIR /app

EXPOSE 8000

RUN adduser -D -H -S django-user
USER django-user