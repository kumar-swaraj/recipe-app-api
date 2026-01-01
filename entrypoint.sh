#!/bin/sh
set -e

echo "Waiting for database..."

until python - <<EOF
import psycopg
psycopg.connect(
    host="${DB_HOST}",
    dbname="${DB_NAME}",
    user="${DB_USER}",
    password="${DB_PASSWORD}",
)
EOF
do
  sleep 2
done

echo "Database is ready"

python manage.py migrate --noinput

exec "$@"