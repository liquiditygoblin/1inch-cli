#!/usr/bin/env bash
git pull
BASE_PATH=$(dirname "$0")
VENV_PATH="$BASE_PATH/.venv/"
$VENV_PATH/bin/python $BASE_PATH/main.py
