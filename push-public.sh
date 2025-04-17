#!/bin/bash

PRIVATE_REPO_PATH="/Users/ashraf/cinemata"
PUBLIC_REPO_PATH="/Users/ashraf/projects/cinematacms-clean"
PUBLIC_REPO_URL="git@github.com:EngageMedia-Tech/cinematacms.git"

rsync -av --delete \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='node_modules' \
  --exclude='vendor' \
  "$PRIVATE_REPO_PATH/" "$PUBLIC_REPO_PATH/"

cd "$PUBLIC_REPO_PATH"

if [ ! -d ".git" ]; then
  echo "Initializing git repo in $PUBLIC_REPO_PATH"
  git init
  git remote add origin "$PUBLIC_REPO_URL"
  git checkout -b main
fi

git add .
git commit -m "Public release from private repo on $(date +'%Y-%m-%d')" || echo "Nothing to commit."

# Check if upstream is set, if not set it
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  git push --set-upstream origin main
else
  git push
fi
