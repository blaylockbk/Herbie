#!/bin/bash

## Brian Blaylock
## December 31, 2020

eval "$(conda shell.bash hook)"
conda activate herbie

# Commit everything before we make Docs
git add -A
git commit -m "updates"

# Make the html docs
make html

# Zip it up for easy download to local computer
cd _build

# Add these changes to GitHub
git add -A
git commit -m "Updated Sphinx Docs"
git push
