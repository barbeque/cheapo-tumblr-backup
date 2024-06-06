#!/bin/bash

set -e

source env/bin/activate
python3 ./scrape.py
mv index.html old-posts.html
mv posts/posts.html index.html
