#!/bin/sh
set -e

echo "Fixing permissions..."
chown -R django-user /vol

echo "Waiting for database..."
until python - <<EOF
import psycopg
psycopg.connect(
    host="$DB_HOST",
    dbname="$DB_NAME",
    user="$DB_USER",
    password="$DB_PASSWORD",
)
EOF
do
  sleep 2
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec su-exec django-user "$@"