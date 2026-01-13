#!/usr/bin/env bash
set -e

cd /opt/flight_tracker

source .venv/bin/activate

# Load env vars (cron does NOT load them)
set -a
source .env
set +a

# Run using the project venv
python -m scripts.run_daily_search