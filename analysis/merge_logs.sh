#!/bin/bash

# Function to merge JSON files in a directory
merge_json_files() {
    local output_file=$1
    shift
    jq -s 'add' "$@" > "$output_file"
    echo "Merged JSON files into $output_file"
}

# Find all CowrieShortTerm directories and merge their JSON files
merged_dir="../logs/COWRIE_SHORT_TERM"
mkdir -p "$merged_dir"
files=$(find ../logs -type f -name "cowrie.json*" -path "../logs/CowrieShortTerm-*")
merge_json_files "$merged_dir/cowrie.json" $files

echo "All JSON files have been merged."
