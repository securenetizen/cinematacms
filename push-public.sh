#!/bin/bash

# Correct paths
PRIVATE_REPO_PATH="/Users/ashraf/cinemata"
PUBLIC_REPO_PATH="/Users/ashraf/projects/cinematacms-clean"
PUBLIC_REPO_URL="git@github.com:EngageMedia-Tech/cinematacms.git"

# Step 1: Sync from private to public folder
rsync -av --delete \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='node_modules' \
  --exclude='vendor' \
  "$PRIVATE_REPO_PATH/" "$PUBLIC_REPO_PATH/"

# Step 2: Initialize git in the public folder if it's not already
cd "$PUBLIC_REPO_PATH"

if [ ! -d ".git" ]; then
  echo "Initializing git repo in $PUBLIC_REPO_PATH"
  git init
  git remote add origin "$PUBLIC_REPO_URL"
  git checkout -b main
fi

# Step 3: Commit and push changes
git add .
git commit -m "Public release from private repo on $(date +'%Y-%m-%d')" || echo "Nothing to commit."
git push -u origin
