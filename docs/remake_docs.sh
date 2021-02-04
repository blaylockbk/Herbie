#!/bin/bash

## Brian Blaylock
## December 31, 2020

## Make Sphinx documents for pyBKB_NRL

# Load the conda environment
#conda activate basic
#conda info

# Make the html docs
make html

# Zip it up for easy download to local computer
cd _build
#zip -q -r html.zip html

# Add these changes to GitHub
git add -A
git commit -m "Updated Sphinx Docs"
git push