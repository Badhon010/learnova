#!/bin/bash
set -e
cd "$(dirname "$0")"
# run.sh is the local development entry point; PythonAnywhere uses WSGI.
export DEBUG="${DEBUG:-True}"
echo "Running migrations..."
python manage.py migrate --run-syncdb
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Starting Learnova Django server on port 5000..."
python manage.py runserver 0.0.0.0:5000
