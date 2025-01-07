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
merge_json_files "$merged_dir/merged.json" $files

echo "CowrieShortTerm JSON files have been merged."

# Merge all json files in COWRIE_BASE
merged_dir="../logs/COWRIE_BASE"
files=$(find ../logs -type f -name "cowrie.json*" -path "../logs/COWRIE_BASE*")
merge_json_files "$merged_dir/merged.json" $files

echo "CowrieBase JSON files have been merged."

# Merge all json files in COWRIE_RANDOM_SSH
merged_dir="../logs/COWRIE_RANDOM_SSH"
files=$(find ../logs -type f -name "cowrie.json*" -path "../logs/COWRIE_RANDOM_SSH*")
merge_json_files "$merged_dir/merged.json" $files

echo "CowrieRandomSSH JSON files have been merged."

for dir in ../logs/CowrieShortTerm-*; do
    merged_dir="$dir"
    files=$(find "$dir" -type f -name "cowrie.json*")
    merge_json_files "$merged_dir/merged.json" $files
    echo "Merged JSON files in $dir"
done
