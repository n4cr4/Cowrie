#!/bin/bash

for dir in ../logs/COWRIE*; do
  if [ -f "${dir}/command_uniq.json" ]; then
    python analyze_command.py --logfile ${dir}/command_uniq.json
  fi
done
