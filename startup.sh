#!/bin/bash

echo "---- Installing Playwright Browsers ----"
python -m playwright install --with-deps chromium

echo "---- Starting Gunicorn Server ----"
gunicorn --bind=0.0.0.0:$PORT app:app
