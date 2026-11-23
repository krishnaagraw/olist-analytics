#!/usr/bin/env bash
# Mac / Linux:  bash run.sh   (add --demo to test with fake data)
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q -r requirements-dev.txt
python run.py "$@"
