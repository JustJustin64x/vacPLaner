#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v brew >/dev/null; then
  echo 'Homebrew fehlt. Alternativ aktuelles Python mit Tk von python.org installieren und eine .venv anlegen.' >&2
  exit 1
fi
brew install python-tk@3.13
planner_python="$(brew --prefix python@3.13)/bin/python3.13"
if [ -e .venv ]; then
  if ! .venv/bin/python -c 'import sys,tkinter; assert sys.version_info >= (3,10) and tkinter.TkVersion >= 8.6'; then
    echo 'Vorhandene .venv ist inkompatibel. Bitte sichern/umbenennen und Setup erneut starten.' >&2
    exit 1
  fi
else
  "$planner_python" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
printf '%s\n' 'Bereit: ./Urlaubsplaner.command oder .venv/bin/python main.py'
