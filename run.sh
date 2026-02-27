#!/usr/bin/env bash

# Start Celery worker in the background
# celery -A config worker --loglevel=info &
# celery -A config worker --loglevel=info --pool=threads &
celery -A config worker --loglevel=info --pool=solo --concurrency=1 &

# Start Gunicorn (Web Server)
# gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2

# celery -A config worker --loglevel=info --pool=threads --concurrency=1

# 3. Wait for processes
