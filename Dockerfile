FROM python:3.13.7-alpine3.22

LABEL maintainer="kumarswaraj"

ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

ARG DEV=false

# --- Pillow + build deps (temporary)
RUN apk add --no-cache --virtual .build-deps \
  build-base \
  jpeg-dev \
  zlib-dev \
  freetype-dev \
  lcms2-dev \
  libwebp-dev \
  tiff-dev

# --- install python deps
COPY requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt

RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r /tmp/requirements.txt && \
  if [ "$DEV" = "true" ]; then \
  /py/bin/pip install -r /tmp/requirements.dev.txt ; \
  fi && \
  rm -rf /tmp && \
  apk del .build-deps

# --- app code
COPY app /app
WORKDIR /app

# --- entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

RUN adduser -D -H -S django-user && \
  mkdir -p /vol/web/static /vol/web/media && \
  chown -R django-user /vol && \
  chmod -R 755 /vol

USER django-user

ENTRYPOINT ["/entrypoint.sh"]