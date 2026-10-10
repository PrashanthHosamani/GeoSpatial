#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 3

if [[ "$*" == *"runserver"* ]]; then
    echo "Creating migrations..."
    python manage.py makemigrations geo_spatial --noinput
    
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

echo "Starting: $@"
exec "$@"
