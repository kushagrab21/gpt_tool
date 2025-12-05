#!/bin/bash

echo "Running local API smoke tests..."
python -m tests.local_api.test_all_engines

