#!/bin/bash

for dir in ../logs/COWRIE*; do
  cd "$dir" || exit
  if [ -f "merged.json" ]; then
    python ../../analysis/vt_report.py
  fi
  cd - || exit
done
