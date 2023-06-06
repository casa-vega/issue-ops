#!/bin/bash

# Check if owner/repo name is supplied as an argument
if [ $# -ne 1 ]; then
    echo "Usage: $0 <owner/repo> )"
    exit 1
fi

OWNER_REPO="$1"
ISSUE_TEMPLATES_DIR=".github/ISSUE_TEMPLATE"

# Generate a random hexadecimal color code
generate_color() {
    printf '%02X%02X%02X\n' $(( RANDOM % 256 )) $(( RANDOM % 256 )) $(( RANDOM % 256 ))
}

# Fetch the existing labels from the repository
EXISTING_LABELS=$(gh api repos/"$OWNER_REPO"/labels --jq '.[].name')

# Convert existing labels to an array
mapfile -t EXISTING_LABELS_ARRAY <<< "$EXISTING_LABELS"

# Iterate over each YAML file in ISSUE_TEMPLATES directory and process new labels
for file in "$ISSUE_TEMPLATES_DIR"/*.yml; do
    # Extract the labels from the YAML file
    mapfile -t labels < <(yq eval '.labels | .[]' "$file")

    for new_label in "${labels[@]}"; do
        # If the new label does not exist in the repository, create it
        if [[ ! " ${EXISTING_LABELS_ARRAY[*]} " =~ ${new_label} ]]; then
            selected_color=$(generate_color)
            gh api repos/"$OWNER_REPO"/labels \
            --method POST \
            --field name="$new_label" \
            --field color="$selected_color"
        fi
    done
done
