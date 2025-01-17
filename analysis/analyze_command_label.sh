#!/bin/bash

for dir in ../logs/COWRIE*; do
    cd $dir || exit
  if [ -f "command_analysis.json" ]; then
    pwd
   jq '
    . | to_entries |
    map(.value.rules | map(.title)) | flatten | unique | length
    ' command_analysis.json
  fi
    cd - || exit
done
