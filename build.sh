#!/usr/bin/env bash
set -euo pipefail

npm install
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-worker.txt
