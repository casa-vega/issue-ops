#!/bin/bash

# Change current working directory to the directory where the script is located
cd "$(dirname "$0")/../.."

# Script to generate form fields, issue template, and composite action for a new operation

# Check if operation name and at least one required field were provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 operation_name required_field1 [required_field2 ...]"
    exit 1
fi

operation_name="$1"
shift 1
required_fields=("$@")

# Create directory for form fields if it doesn't exist
mkdir -p .github/FORM_FIELDS

# Create directory for issue templates if it doesn't exist
mkdir -p .github/ISSUE_TEMPLATE

# Create directory for actions if it doesn't exist
mkdir -p .github/actions/$operation_name

# Generate form fields
echo "required_fields:" > .github/FORM_FIELDS/$operation_name.yml
for field in "${required_fields[@]}"; do
    echo "  - $field" >> .github/FORM_FIELDS/$operation_name.yml
done

# Generate issue template
cat > .github/ISSUE_TEMPLATE/$operation_name.yml << EOL
name: $operation_name
description: Description for $operation_name
title: "[$operation_name] Title for $operation_name"
labels:
  - $operation_name
body:
EOL

for field in "${required_fields[@]}"; do
    cat >> .github/ISSUE_TEMPLATE/$operation_name.yml << EOL
  - type: input
    id: $field
    attributes:
      label: $field (*)
      description: Description for $field
      placeholder: ex. value
EOL
done

# Generate composite action
cat > .github/actions/$operation_name/action.yml << EOL
name: $operation_name
author: "@github"
description: Description for $operation_name

inputs:
EOL

for field in "${required_fields[@]}"; do
    cat >> .github/actions/$operation_name/action.yml << EOL
  $field:
    description: "Description for $field"
    required: true
EOL
done

cat >> .github/actions/$operation_name/action.yml << EOL
runs:
  using: composite
  steps:
    - name: Execute $operation_name
      shell: bash
      run: |
        echo "Add your code here to execute the operation"
EOL
