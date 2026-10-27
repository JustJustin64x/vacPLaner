#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Bitte zuerst im Terminal: bash scripts/setup-macos.sh'
  read -r -p 'Enter zum Schließen ' answer
  exit 1
fi
exec .venv/bin/python main.py
