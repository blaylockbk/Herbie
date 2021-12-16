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

# Add these changes to GitHub
git add -A
git commit -m "Updated Sphinx Docs"
git push
