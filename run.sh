#!/usr/bin/env bash
# Creates a virtual environment (first run only), installs dependencies and starts the API.
set -e
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload
