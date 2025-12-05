#!/bin/bash

echo "Starting local CA Super Tool server on port 8000..."

# Replace shell with uvicorn so PID is correct and killable
exec uvicorn ca_super_tool.main:app --port 8000

