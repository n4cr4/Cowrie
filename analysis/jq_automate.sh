#!/bin/bash

for dir in ../logs/COWRIE*; do
    cd $dir || exit
  if [ -f "command_analysis.json" ]; then
    pwd
    echo "Number of unique commands label:"
    jq '
    . | to_entries |
    map(.value.rules | map(.title)) | flatten | unique | length
    ' command_analysis.json

    echo "Number of unique vt label:"
    jq 'keys | length' vt_label.json

    echo "Number of unique vt category:"
    jq 'keys | length' vt_category.json

    echo "Number of unique ip:"
    jq '.ips | keys | length' ip_stats.json

    echo "Number of unique client version:"
    jq '.client_versions | keys | length' client_version.json
  fi
    cd - || exit
done
