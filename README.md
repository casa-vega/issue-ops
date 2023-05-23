# GitHub Issue Operations via Actions

![Code Coverage](https://img.shields.io/badge/Coverage-100%25-green.svg)

In this repository, we employ GitHub Issue Operations (Issue Ops) via GitHub Actions to facilitate a user-requested, self-service approach to GitHub features. This strategy optimizes our workflow by automating actions in response to issue interactions, effectively enabling users to request changes without requiring direct owner access. For instance, users can initiate the addition of a webhook to the repository simply by creating a specific issue. Upon detecting the creation of this issue the associated GitHub Action would validate the request and automatically add the webhook, thereby preserving user autonomy and ensuring a secure, efficient, and collaborative environment.

---

## A self-service approach for managing github components/settings across MULTIPLE instances of GitHub and GitHub Enterprise.

### Getting Started

#### Multiple GitHub Instances

Supporting multiple GitHub Instances is done via form. It's not uncommon for large enterprises to have multiple instances of GitHub. In these cases users choose the instance they want to perform the work. There is no secret sauce, we just propagate the instance name provided to our validation code which will return the hostname of the target. See the `validation.py` docs below to learn more.

Create GitHub tokens that have the level of access you require. Do that for each instance. We use and also advocate using the `gh` tool with the ` --with-token < token.txt` CLI tool in most cases, now that we have a parsed instance name from the form, this allows us to ask for a repository secret like `GHES_TOKEN` in a slightly dynamic way:

```
echo \
${{ secrets[format('{0}_TOKEN', steps.parser.output.instance )] }} \
> token.txt
```

Followed by:

```bash
gh auth login \
--with-token < token.txt
rm token.txt
```

#### Creating a new issue operation for users

1. Think about the operation you want to perform in contrast with GitHub API's. If you have an endpoint that enables you to modify components or features of GitHub, that will be a good candidate for moving forward. When thinking about this project, new issue ops require the creation of the following three files, and an issue label

##### base requirements:

> ###### A list of required form fields
> `.github/FORM_FIELDS/repo-create-archive.yml`
> ###### The issue template
> `.github/ISSUE_TEMPLATE/repo-create-archive.yml`
> ###### Composite action to perform the issue operation
> `.github/actions/repo-create-archive/action.yml`
> ###### Issue label
> `repo-create-archive`
> ###### Workflow permissions
> `Read and Write Permissions` must be set in the organization settings
> ###### Secrets
> Repo secrets are typically service account personal access tokens that have administrative privledge to the target instance

2. Since the API will typically require inputs you'll want to ensure you create an `ISSUE_TEMPLATE/` that encapsulates those API requirements using a form. For more information on using templates see: [Configuring issue templates for your repository](https://docs.github.com/en/enterprise-cloud@latest/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)

3. Create an `ISSUE_TEMPLATE/`, here's an example of an operation that will archive a repo. Take note of the `id:` key. When we parse the issue template we will be able to use the `id:` names as step output in other steps.

```yaml
name: "[Repo] - archive a repository"
description: set a repo to archived making it read only
title: "[repo-create-archive] Archive a repository"
labels:
  - repo-create-archive
body:
  - type: dropdown
    id: instance
    attributes:
      label: GitHub Instance (*)
      description: The instance of Github you're targeting. 
      options:
        - COM
        - EMU
        - SOMA
  - type: input
    id: organization
    attributes:
      label: GitHub Organization (*)
      description: The name of the github organization (must be exact)
      placeholder: ex. github
  - type: input
    id: repository
    attributes:
      label: GitHub Repository (*)
      description: The name of the github repository (must be exact)
      placeholder: ex. actions

```

4. If you're running in a `public` repo you can set form fields as required. In `private` and `internal` repos this is not possible yet.

To ensure forms can adhere to required values, is it possible to set these values in `FORM_FIELDS`. We will programmatically check these values at runtime and prevent any work from occuring when the required fields are not present.

To use this feature, create a `yml` file that matches the issue template file name. Above we used the repo archive operation (`ISSUE_TEMPLATE/repo-archive.yml`), this is what a corresponding `FORM_FIELDS/repo-archive.yml` would look like:

```yaml
required_fields:
  - instance
  - organization
  - repository
```

In this example we require every value in the issue template to be present when calling the api.

5. Create your composite action. Here's what the example repo-archive composite action would look like:
```yml
name: repo-create-archive

inputs:
  instance:
    description: "GitHub Instance"
    required: true
  organization:
    description: "GitHub Organization"
    required: true
  repository:
    description: "GitHub Repository"
    required: true

runs:
  using: composite
  steps:
    - name: archive a repository
      shell: bash
      run: |
        $data=(gh api repos/${{ inputs.organization }}/${{ inputs.repository }} \
          --input - <<< '{
            "archived": true
          }')
        if [[ $? -eq 0 ]]; then
          json_data=$(jq -nc '{ "msg": "Create repo archive successful", "status": "success" }')
          echo -e "RESULT=$json_data" >> $GITHUB_ENV
        else
          json_data=$(jq -nc --arg error "$data" '{ "msg": "Unable to archive repository", "status": "failure", "error": $error }')
          echo -e "RESULT=$json_data" >> $GITHUB_ENV
        fi
```
## Layout / Architecture:
Issue ops lives inside the .github directory at the base of the repo. The framework itself relies on builtin GitHub constructs for `workflow/`, `ISSUE_TEMPLATES` directories and a best practice approach for `scripts/`. The only unique pieces of data are `ENTITLEMENTS/github.yml`, and `FORM_FIELDS`.

```bash
├── ENTITLEMENTS
│   └── github.yml
├── FORM_FIELDS
│   ├── repo-create-archive.yml
│   ├── ...
├── ISSUE_TEMPLATE
│   ├── config.yml
│   ├── repo-create-archive.yml
│   ├── ...
├── actions
│   ├── issue-op
│   │   └── action.yml
│   └── repo-create-archive
│       └── action.yml
│   └── ...
├── scripts
│   ├── .coveragerc
│   ├── validation.py
│   └── validation_test.py
└── workflows
    └── issue-ops.yml
```

### `actions/`

Issue operations are comprised on GitHub composite actions. For every composite action an `actions.yml` exists. The composite action has a set of inputs it expects and executes the request. The request is typically executed using `gh` cli tool but doesn't have to be.

As you can see below the org webhook action remains fairly small and it's clear what will be executed coupled with messaging that can we can bubble up.

```yaml
- name: archive a repository
  shell: bash
  run: |
    $data=(gh api repos/${{ inputs.organization }}/${{ inputs.repository }} \
      --input - <<< '{
        "archived": true
    }')
    if [[ $? -eq 0 ]]; then
      json_data=$(jq -nc '{ "msg": "Create repo archive successful", "status": "success" }')
      echo -e "RESULT=$json_data" >> $GITHUB_ENV
    else
      json_data=$(jq -nc --arg error "$data" '{ "msg": "Unable to archive repository", "status": "failure", "error": $error }')
      echo -e "RESULT=$json_data" >> $GITHUB_ENV
    fi
```
#### Dynamic Uses

The `uses:` directive in actions is not dynamic. This means you need to use `if` logic to determine the operation you want to run. This tends to pollute the actions log with a bunch of action steps that don't get run and we probably want to avoid that as operations increase in volume.

To avoid this we call a composite action that creates another composite action on the fly with our dynamic actions path. This allows us to call that composite action directly bypassing the need to determine which action downstream should be run.

I modified to https://github.com/jenseng/dynamic-uses to preprocess `JSON` ahead of time which makes our composite actions more explicit and easier to understand.

---

### `ENTITLEMENTS/github.yml`
This directory has a single entitlements file that is specific to each target github instance. This file is used to validate against to determine if an org exists within an instance and if a user has entitlements to that organization. It's used in conjunction with `validate.py auth`.

```yml
github_instances:
  - instance: COM
    url: github.com
    organizations:
      - name: avocado-corp
        owners:
          - octocat
      - name: thehub
        owners:
          - hubber
  - instance: EMU
    url: github.com
    organizations:
      - name: enterprise-org
        owners:
          - mona
  - instance: GHES
    url: https://private.github.internal
    organizations:
      - name: enterprise-org-onprem
        owners:
          - jdoe
```
---

### `FORM_FIELDS/`
This directory houses YAML files that define the requisite form fields. Each file within this directory should adhere to the ISSUE_TEMPLATE naming convention and encompass a list of parsed issue identifiers. This is used in conjunction with `validation.py form` to ensure prohibited values are not present before making any requests or performing any production changes.

```yml
required_fields:
  - instance
  - organization
  - repository
```
---
### `scripts/`
#### `validation.py`
This script is designed to consistently satisfy a few critical use cases

#### Authentication:
- Validates the organization and verifies user entitlements to the organization using ENTITLEMENTS/github.yml.
  - Throws an error for invalid organizations.
  - Throws an error when the user lacks necessary entitlements.
#### Form Validation:
- Ensures that the issue does not contain prohibited values (e.g., None, "", []). A required field must never be empty.
  - Throws an error when prohibited values are detected.
#### Hostname Resolution:
- This function furnishes a monolithic JSON object that serves as the data source for populating the operations requests

##### Additional notes:
`ENTITLEMENTS/github.yml` and `FORM_FIELDS` are sources of truth so it is worth noting that some of these values within validation.py are hardcoded. They could easily be moved to a config file if needed, but this ensures validation.py is always using the expected filesystem locations and expected sources.


##### validation.py auth
```
python .github/scripts/validation.py auth --help
usage: validation.py auth [-h] -i INSTANCE -o ORG -u USER

options:
  -h, --help            show this help message and exit
  -i INSTANCE, --instance INSTANCE
                        Name of the GitHub instance
  -o ORG, --org ORG     Name of the organization
  -u USER, --user USER  user (github.actor) to validate
```
##### validation.py form
```
python .github/scripts/validation.py form --help
usage: validation.py form [-h] -o OP

options:
  -h, --help      show this help message and exit
  -o OP, --op OP  The issue op name
```
##### validation.py payload
```
python .github/scripts/validation.py payload --help
usage: validation.py payload [-h] -i INSTANCE

options:
  -h, --help            show this help message and exit
  -i INSTANCE, --instance INSTANCE
                        Name of the GitHub instance
```

##### validation.py unittest coverage
```
Name                 Stmts   Miss  Cover
----------------------------------------
validation.py          111      1    99%
validation_test.py     209      0   100%
----------------------------------------
TOTAL                  320      1    99%
```


---
### Issue Ops Workflow
```mermaid
%%{ init : {
  "theme" : "dark",
  "flowchart" : {
    "padding": 10,
    "nodeSpacing": 20,
    "rankSpacing": 15
  }
}}%%
flowchart
	733212["Issue parsed"] --- 687741{"Request\nValidated"}
	164276["Issue updated"] --- 862296(["Issue Closed"])
	817495["Create Object"] --- 319413["Configure gh"]
	319413 --- 721800["Execute step"]
	687436(["Issue Created"]) --- 297482["Action triggered"]
	297482 --- 733212
	721800 --- 473259["Issue updated"]
	473259 --- 379849(["Issue Closed"])
	687741 ---|"Valid"| 817495
	687741 ---|"Invalid"| 164276
```
