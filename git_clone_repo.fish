#!/usr/bin/env fish

set -l dir_parent (dirname "$GITHUB_WORKSPACE")
mkdir -p "$dir_parent"
cd "$dir_parent"
rm -rf "$GITHUB_WORKSPACE"
git clone "git@github.com:$GITHUB_REPOSITORY.git"
cd "$GITHUB_WORKSPACE"
git remote -v
ls -lha
