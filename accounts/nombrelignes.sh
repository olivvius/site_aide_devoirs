#!/bin/bash

find . -name "*.py" -type f | xargs wc -l | tail -n 1
echo "lignes python"
find . -name "*.html" -type f | xargs wc -l | tail -n 1
echo "lignes html"
