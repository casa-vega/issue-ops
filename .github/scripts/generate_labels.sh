#!/bin/bash

issue_templates_dir=".github/ISSUE_TEMPLATE"
labels_array=()

# Get a list of YAML files in the ISSUE_TEMPLATES directory
yaml_files=( "$issue_templates_dir"/*.yml )

# Iterate over each YAML file
for file in "${yaml_files[@]}"; do
    # Extract the keys from the "labels" key using yq and append them to the array
    labels=$(yq eval '.labels | .[]' "$file")
    labels_array+=( $labels )
done

# Print the collected keys
echo "Collected keys:"
for key in "${labels_array[@]}"; do
    echo "$key"
done