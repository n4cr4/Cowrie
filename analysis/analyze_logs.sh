#!/bin/bash

for dir in ../logs/COWRIE*; do
  cd "$dir" || exit
  if [ -f "merged.json" ]; then
    python ../../analysis/analysis.py --logfile merged.json
  fi
  cd - || exit
done
