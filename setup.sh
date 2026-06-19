#!/usr/bin/env bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install
echo "Setup complete."
