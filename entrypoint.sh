#!/bin/sh
set -e

echo "Waiting for PostgreSQL database container..."
if [ "$DB_HOST" = "db" ]; then
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done
    echo "PostgreSQL database is ready!"
fi

echo "Applying Django Database Migrations..."
python manage.py migrate --noinput

echo "Seeding Master Data & Default Enterprise Workflows..."
python manage.py seed_data

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

exec "$@"
