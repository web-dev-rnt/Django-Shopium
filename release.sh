#!/bin/bash
set -e

echo ">>> Running database migrations..."
python manage.py migrate --noinput

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Starting gunicorn..."
exec gunicorn Shopium.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120
