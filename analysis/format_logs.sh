#!/bin/bash

# Function to format JSON files using jq
format_json_files() {
    local dir=$1
    for file in "$dir"/*.json*; do
        if [[ -f $file ]]; then
            echo "Formatting $file"
            jq -s '.' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
        fi
    done
}

# Iterate over all directories in logs
for dir in ../logs/*; do
    if [[ -d $dir ]]; then
        format_json_files "$dir"
    fi
done

echo "All JSON files have been formatted."
