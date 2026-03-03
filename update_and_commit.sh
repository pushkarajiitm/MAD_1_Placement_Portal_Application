#!/usr/bin/env bash

# Delete existing index if existing
if [ -f .git/index.lock ]; then rm .git/index.lock; fi
# Add tracked changes only
git add .
error_count=0

# Create simple commit if we have changes
if ! git commit -a -m "Added student features and enhanced dashboard UI." --allow-empty; then error_count=1; fi
