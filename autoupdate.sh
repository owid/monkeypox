#!/bin/bash
set -e
BRANCH="main"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# FUNCTIONS
has_changed() {
  git diff --name-only --exit-code $1 >/dev/null 2>&1
  [ $? -ne 0 ]
}

git_push() {
  if [ -n "$(git status --porcelain)" ]; then
    msg="data("$1"): automated update"
    git add .
    git commit -m "$msg"
    git push
  fi
}

# Move to the root directory
cd $SCRIPT_DIR

# Activate Python virtualenv
source venv/bin/activate

# Make sure we have the latest commit.
git reset --hard origin/master && git pull

# Run script
python monkeypox.py
if has_changed 'owid-monkeypox-data.csv'; then
  git_push "mpx"
else
  echo "Global.health data is up to date"
fi
