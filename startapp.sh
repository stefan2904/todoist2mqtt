#!/bin/bash

echo Starting Gunicorn.

exec gunicorn app:app \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --log-level info
