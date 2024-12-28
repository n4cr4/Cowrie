#!/bin/bash

for dir in ../logs/COWRIE*/reports; do
  cd "$dir" || exit
  jq -s '. | map({
    category: [.data.attributes.popular_threat_classification.popular_threat_category[]?.value // empty],
    name: [.data.attributes.popular_threat_classification.popular_threat_name[]?.value // empty],
    label: (.data.attributes.popular_threat_classification.suggested_threat_label // "N/A"),
    tags: (.data.attributes.tags // []),
    magic: (.data.attributes.magic // ""),
    id: (.data.id // ""),
    last_analysis_status: (.data.attributes.last_analysis_status // {})
  })' *.json > ../vt.json
  cd - || exit
done
