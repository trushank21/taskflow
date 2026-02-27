#!/usr/bin/env bash

# Start Celery worker in the background
# celery -A config worker --loglevel=info &
celery -A config worker --loglevel=info --pool=threads &

# Start Gunicorn (Web Server)
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

celery -A config worker --loglevel=info --pool=threads --concurrency=1

# 3. Wait for processes
wait -n