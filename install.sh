#!/usr/bin/env bash

# Exit immediately if a pipeline (see Pipelines), which may consist of a single simple command (see Simple Commands), a list (see Lists of Commands), or a compound command (see Compound Commands) returns a non-zero status.
set -e

case "$OSTYPE" in
  linux*)
    echo "### Starting installation of Goblin Trading CLI...";;
  *)
    echo "This script only works on linux for now."; exit 1;;
#   solaris*) echo "SOLARIS" ;;
#   darwin*)  echo "OSX" ;; 
#   bsd*)     echo "BSD" ;;
#   msys*)    echo "WINDOWS" ;;
#   cygwin*)  echo "ALSO WINDOWS" ;;
esac


REPO_URL="https://github.com/liquiditygoblin/1inch-cli"
REPO_PATH="./1inch-cli/"
VENV_PATH="./.venv/"

# Tries to install python3, git and virtualenv. If they're already installed, nothing happens
sudo apt -qq update
sudo apt -qq install python3 git python3-virtualenv -y

# If repo directory doesn't exist, clone the repo
if [ ! -d "$REPO_PATH" ]; then
  git clone $REPO_URL
fi

cd $REPO_PATH


if [ ! -d "$VENV_PATH" ] || [ ! -f "$VENV_PATH/bin/activate" ]; then
    # Create virtualenv inside project folder
    python3 -m virtualenv -p python3 $VENV_PATH
fi

# Source virtualenv
. $VENV_PATH/bin/activate

# Install python requirements
$VENV_PATH/bin/python -m pip install -r requirements.txt -q

# Makes main.py executable
chmod u+x run.sh


echo "Goblin Trading CLI installed"
echo "To run Goblin Trading CLI simply execute ./run.sh"
