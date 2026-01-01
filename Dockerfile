FROM python:3.13.7-alpine3.22

LABEL maintainer="kumarswaraj"

ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

# --- build-time args
ARG DEV=false

# --- install python deps first (best cache leverage)
COPY requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt

RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install -r /tmp/requirements.txt && \
  if [ "$DEV" = "true" ]; then \
  /py/bin/pip install -r /tmp/requirements.dev.txt ; \
  fi && \
  rm -rf /tmp

# --- app code
COPY app /app
WORKDIR /app

# --- entrypoint (copied after deps to avoid cache bust)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# --- non-root user LAST
RUN adduser -D -H -S django-user
USER django-user

ENTRYPOINT ["/entrypoint.sh"]