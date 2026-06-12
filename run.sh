#!/bin/bash
set -e
cd /home/runner/workspace/learnova_django
echo "Running migrations..."
python manage.py migrate --run-syncdb
echo "Starting Learnova Django server on port 5000..."
python manage.py runserver 0.0.0.0:5000
