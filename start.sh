#!/bin/bash
# Start script for CA Super Tool
# Uses gunicorn with uvicorn worker class for production

gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

