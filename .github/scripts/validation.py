import argparse
import json
import os
from typing import Dict, List, Any, Optional
import yaml


class Form:
    """
    Class for form validation.
    """

    prohibited_values: List[str] = ["None", "", "[]"]

    @staticmethod
    def validate_fields(
        data: Dict[str, Any], fields: List[str], errors: Dict[str, Any]
    ) -> None:
        """
        Validates the form data against the specified fields and prohibited values.

        Parameters
        ----------
        data : Dict[str, Any]
            The form data as a dictionary.
        fields : List[str]
            The required fields as a list of strings.
        errors : Dict[str, Any]
            A dictionary to store any validation errors.
        """
        prohibited_value_errors = []
        for key in fields:
            value = data.get(key)
            if str(value) in Form.prohibited_values:
                prohibited_value_errors.append({key: value})
        if prohibited_value_errors:
            errors["prohibited_values"] = prohibited_value_errors


class Auth:
    """
    Class for GitHub authentication validation.
    """

    @staticmethod
    def find_organization(
        instance: Dict[str, Any], organization_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the organization within the given instance.

        Parameters
        ----------
        instance : Dict[str, Any]
            The instance data as a dictionary.
        organization_name : str
            The name of the organization.

        Returns
        -------
        Dict[str, Any] or None
            The organization data if found, otherwise None.
        """
        return next(
            (
                org
                for org in instance["organizations"]
                if org["name"] == organization_name
            ),
            None,
        )


    @staticmethod
    def is_owner(organization: Dict[str, Any], username: str) -> bool:
        """
        Checks if the given username is an owner of the organization.

        Parameters
        ----------
        organization : Dict[str, Any]
            The organization data as a dictionary.
        username : str
            The username.

        Returns
        -------
        bool
            True if the username is an owner, otherwise False.
        """
        return username in organization["owners"]


    @staticmethod
    def validate_user(
        instance_list: Dict[str, Any],
        github_instance: str,
        organization_name: str,
        username: str,
    ) -> Dict[str, str]:
        """
        Validates the GitHub instance, organization, and user.

        Parameters
        ----------
        instance_list : Dict[str, Any]
            The list of instances as a dictionary.
        github_instance : str
            The name of the GitHub instance.
        organization_name : str
            The name of the organization.
        username : str
            The username.

        Returns
        -------
        Dict[str, str]
            A dictionary of validation errors if any errors were found, otherwise an empty dictionary.
        """
        error_messages = {}

        target = next(
            (
                instance
                for instance in instance_list["github_instances"]
                if instance["instance"] == github_instance
            ),
            None,
        )

        if target is None:
            error_messages["instance_error"] = f"invalid github instance: {github_instance}"
        else:
            organization = Auth.find_organization(target, organization_name)
            if not organization:
                error_messages[
                    "organization_error"
                ] = f"invalid organization: {organization_name}"
            elif not Auth.is_owner(organization, username):
                error_messages["auth_error"] = f"user does not have permissions: {username}"
        return error_messages


def auth(args: argparse.Namespace) -> None:
    """
    Handles the 'auth' command.

    Parameters
    ----------
    args : argparse.Namespace
        The command-line arguments.
    """
    instance_list = read_yaml(".github/ENTITLEMENTS/github.yml")
    errors = Auth.validate_user(
        instance_list, args.instance, args.org, args.user
    )
    if errors:
        print(json.dumps(errors))


def form(args: argparse.Namespace) -> None:
    """
    Handles the 'form' command.

    Parameters
    ----------
    args : argparse.Namespace
        The command-line arguments.
    """
    with open(f"{os.environ.get('HOME')}/issue-parser-result.json") as f:
        json_data = json.load(f)

    yaml_data = read_yaml(f".github/FORM_FIELDS/{args.op}.yml")
    fields = yaml_data.get("required_fields", [])
    errors = {}
    Form.validate_fields(json_data, fields, errors)
    if errors:
        print(json.dumps(errors))


def hostname(gh: str) -> str: # type: ignore
    """
    Prints the URL of the given GitHub instance.

    Parameters
    ----------
    args : argparse.Namespace
        The command-line arguments.
    """
    data = read_yaml(".github/ENTITLEMENTS/github.yml")
    for instance in data['github_instances']:
        if instance['instance'] == gh:
            return instance['url']


def owners(args: argparse.Namespace) -> Optional[List[str]]:
    """
    Extract the owners of an organization from a YAML file.

    Parameters
    ----------
    yaml_file : str
        The path to the YAML file.
    org_name : str
        The name of the organization.

    Returns
    -------
    list or None
        The list of owners if the organization is found; None otherwise.

    """
    data = read_yaml(".github/ENTITLEMENTS/github.yml")

    for instance in data['github_instances']:
        for org in instance['organizations']:
            if org['name'] == args.org:
                return org['owners']

    return None

def json_data() -> None:
    """
    Handles the 'json_data' command which prints a JSON object to stdout.

    Parameters
    ----------
    args : argparse.Namespace
        The command-line arguments.
    """
    with open(f"{os.environ.get('HOME')}/issue-parser-result.json") as f:
        json_data = json.load(f)
    print(f"{json.dumps(json_data)}")


def read_json(file_path: str) -> Dict[str, Any]:
    """
    Reads a JSON file.

    Parameters
    ----------
    file_path : str
        The path to the JSON file.

    Returns
    -------
    Dict[str, Any]
        The JSON data as a Python object.
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not valid JSON.")
        exit(1)


def read_yaml(file_path: str) -> Dict[str, Any]:
    """
    Reads a YAML file.

    Parameters
    ----------
    file_path : str
        The path to the YAML file.

    Returns
    -------
    Dict[str, Any]
        The YAML data as a Python object.
    """
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        exit(1)
    except yaml.YAMLError:
        print(f"Error: The file {file_path} is not valid YAML.")
        exit(1)


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns
    -------
    argparse.Namespace
        The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="issue ops validation tool")
    subparsers = parser.add_subparsers()

    auth_parser = subparsers.add_parser("auth", help="Auth help")
    auth_parser.add_argument(
        "-i",
        "--instance",
        required=True,
        help="Name of the GitHub instance"
    )
    auth_parser.add_argument(
        "-o",
        "--org",
        required=True,
        help="Name of the organization"
    )
    auth_parser.add_argument(
        "-u",
        "--user",
        required=True,
        help="user (github.actor) to validate"
    )
    auth_parser.set_defaults(func=auth)

    form_parser = subparsers.add_parser("form", help="Form help")
    form_parser.add_argument(
        "-o",
        "--op",
        required=True,
        help="The issue op name"
    )
    form_parser.set_defaults(func=form)

    form_parser = subparsers.add_parser("json", help="JSON help")
    form_parser.add_argument(
        "-i",
        "--instance",
        required=True,
        help="Name of the GitHub instance"
    )
    form_parser.set_defaults(func=json_data)

    form_parser = subparsers.add_parser("host", help="Host help")
    form_parser.add_argument(
        "-i",
        "--instance",
        required=True,
        help="Name of the GitHub instance"
    )
    form_parser.set_defaults(func=hostname)

    form_parser = subparsers.add_parser("owners", help="Host help")
    form_parser.add_argument(
        "-o",
        "--org",
        required=True,
        help="Name of the GitHub instance"
    )
    form_parser.set_defaults(func=hostname)


    return parser.parse_args()

def main():
    args = parse_arguments()
    args.func(args)

if __name__ == "__main__":
    main()
