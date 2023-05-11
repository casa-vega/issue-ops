import argparse
import unittest
from unittest.mock import patch, mock_open
import argparse
import json
import yaml

from validation import (
    Form,
    Auth,
    hostname,
    read_json,
    read_yaml,
    form,
    auth,
    parse_arguments,
    main,
)


class TestForm(unittest.TestCase):
    def test_validate_fields(self):
        data = {
            "username": "john-doe",
            "repository": "github-repo",
            "issue_title": "",
            "issue_body": "None",
        }
        fields = ["username", "repository", "issue_title", "issue_body"]
        errors = {}
        Form.validate_fields(data, fields, errors)
        self.assertEqual(
            errors, {"prohibited_values": [{"issue_title": ""}, {"issue_body": "None"}]}
        )


class TestAuth(unittest.TestCase):
    def test_validate_user_instance_error(self):
        instance_list = {
            "github_instances": [
                {
                    "instance": "Github2",
                    "organizations": [{"name": "Org1", "owners": ["User1"]}],
                }
            ]
        }
        errors = Auth.validate_user(instance_list, "Github1", "Org1", "User1")
        self.assertEqual(errors, {"instance_error": "invalid github instance: Github1"})

    def test_validate_user_organization_error(self):
        instance_list = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org2", "owners": ["User1"]}],
                }
            ]
        }
        errors = Auth.validate_user(instance_list, "Github1", "Org1", "User1")
        self.assertEqual(errors, {"organization_error": "invalid organization: Org1"})

    def test_validate_user_auth_error(self):
        instance_list = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org1", "owners": ["User2"]}],
                }
            ]
        }
        errors = Auth.validate_user(instance_list, "Github1", "Org1", "User1")
        self.assertEqual(
            errors, {"auth_error": "user does not have permissions: User1"}
        )

    def test_validate_user_all_pass(self):
        instance_list = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org1", "owners": ["User1"]}],
                }
            ]
        }
        errors = Auth.validate_user(instance_list, "Github1", "Org1", "User1")
        self.assertEqual(errors, {})

    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_auth_instance_error(self, mock_print, mock_read_yaml):
        args = argparse.Namespace()
        args.instance = "Github1"
        args.org = "Org1"
        args.user = "User1"
        mock_read_yaml.return_value = {
            "github_instances": [
                {
                    "instance": "Github2",
                    "organizations": [{"name": "Org1", "owners": ["User1"]}],
                }
            ]
        }
        auth(args)
        mock_print.assert_called_once_with(
            '{"instance_error": "invalid github instance: Github1"}'
        )

    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_auth_organization_error(self, mock_print, mock_read_yaml):
        args = argparse.Namespace()
        args.instance = "Github1"
        args.org = "Org1"
        args.user = "User1"
        mock_read_yaml.return_value = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org2", "owners": ["User1"]}],
                }
            ]
        }
        auth(args)
        mock_print.assert_called_once_with(
            '{"organization_error": "invalid organization: Org1"}'
        )

    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_auth_auth_error(self, mock_print, mock_read_yaml):
        args = argparse.Namespace()
        args.instance = "Github1"
        args.org = "Org1"
        args.user = "User1"
        mock_read_yaml.return_value = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org1", "owners": ["User2"]}],
                }
            ]
        }
        auth(args)
        mock_print.assert_called_once_with(
            '{"auth_error": "user does not have permissions: User1"}'
        )

    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_auth_no_errors(self, mock_print, mock_read_yaml):
        args = argparse.Namespace()
        args.instance = "Github1"
        args.org = "Org1"
        args.user = "User1"
        mock_read_yaml.return_value = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org1", "owners": ["User1"]}],
                }
            ]
        }
        auth(args)
        mock_print.assert_not_called()

    @patch("validation.read_yaml")
    @patch("json.load")
    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Form, "validate_fields")
    def test_form_with_errors(
        self, mock_validate, mock_file, mock_json_load, mock_read_yaml
    ):
        args = argparse.Namespace()
        args.op = "Github1"
        mock_json_load.return_value = {"address": None}
        mock_read_yaml.return_value = {"required_fields": ["address"]}
        mock_validate.side_effect = lambda data, fields, errors: errors.update(
            {"prohibited_values": [{"address": None}]}
        )
        with patch("builtins.print") as mock_print:
            form(args)
        mock_print.assert_called_once_with('{"prohibited_values": [{"address": null}]}')

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"name": "John", "age": "25", "address": "123 street"}',
    )
    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_form_without_errors(self, mock_print, mock_read_yaml, mock_file):
        args = argparse.Namespace()
        args.op = "Github1"
        mock_read_yaml.return_value = {"required_fields": ["name", "age", "address"]}
        form(args)
        mock_print.assert_not_called()


class TestFunctions(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_read_json(self, mock_file):
        data = read_json("dummy_path")
        self.assertEqual(data, {"key": "value"})

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("json.load")
    def test_read_json_file_not_found(self, mock_json, mock_file):
        mock_file.side_effect = FileNotFoundError
        with self.assertRaises(SystemExit) as cm:
            with patch("builtins.print") as mock_print:
                read_json("dummy_path")
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_once_with("Error: The file dummy_path does not exist.")

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("json.load")
    def test_read_json_decode_error(self, mock_json, mock_file):
        mock_json.side_effect = json.JSONDecodeError("Dummy error", doc="", pos=0)
        with self.assertRaises(SystemExit) as cm:
            with patch("builtins.print") as mock_print:
                read_json("dummy_path")
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_once_with(
            "Error: The file dummy_path is not valid JSON."
        )

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("yaml.safe_load")
    def test_read_yaml(self, mock_safe_load, mock_file):
        mock_safe_load.return_value = {"key": "value"}
        result = read_yaml("dummy.yaml")
        self.assertEqual(result, {"key": "value"})

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("yaml.safe_load")
    def test_read_yaml_file_not_found(self, mock_safe_load, mock_file):
        mock_file.side_effect = FileNotFoundError
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                read_yaml("dummy.yaml")
        mock_print.assert_called_once_with("Error: The file dummy.yaml does not exist.")

    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    @patch("yaml.safe_load")
    def test_read_yaml_decode_error(self, mock_safe_load, mock_file):
        mock_safe_load.side_effect = yaml.YAMLError
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                read_yaml("dummy.yaml")
        mock_print.assert_called_once_with(
            "Error: The file dummy.yaml is not valid YAML."
        )

    @patch("validation.read_yaml")
    @patch("builtins.print")
    def test_hostname(self, mock_print, mock_read_yaml):
        args = argparse.Namespace()
        args.instance = "Github1"
        # Mock yaml.safe_load to return a nested dictionary
        mock_read_yaml.return_value = {
            "github_instances": [{"instance": "Github1", "url": "http://github1.com"}]
        }
        hostname(args)
        mock_print.assert_called_once_with("http://github1.com")

    @patch.object(argparse.ArgumentParser, "parse_args")
    def test_parse_arguments_auth(self, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            instance="Github1",
            org="Org1",
            user="User1",
            func=auth,
        )
        args = parse_arguments()
        self.assertEqual(args.instance, "Github1")
        self.assertEqual(args.org, "Org1")
        self.assertEqual(args.user, "User1")
        self.assertEqual(args.func, auth)

    @patch.object(argparse.ArgumentParser, "parse_args")
    def test_parse_arguments_form(self, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            instance="Github1",
            func=form,
        )
        args = parse_arguments()
        self.assertEqual(args.instance, "Github1")
        self.assertEqual(args.func, form)

    @patch.object(argparse.ArgumentParser, "parse_args")
    def test_parse_arguments_hostname(self, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            instance="Github1",
            func=hostname,
        )
        args = parse_arguments()
        self.assertEqual(args.instance, "Github1")
        self.assertEqual(args.func, hostname)

    @patch("validation.read_yaml")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("builtins.print")
    def test_main_auth(self, mock_print, mock_parse_args, mock_read_yaml):
        mock_parse_args.return_value = argparse.Namespace(
            instance="Github1",
            org="Org1",
            user="User1",
            func=auth,
        )
        mock_read_yaml.return_value = {
            "github_instances": [
                {
                    "instance": "Github1",
                    "organizations": [{"name": "Org1", "owners": ["User1"]}],
                }
            ]
        }
        main()
        mock_print.assert_not_called()  # assert that no errors were printed

    @patch("validation.read_yaml")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("builtins.print")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"name": "John", "age": "25"}',
    )
    def test_main_form(self, mock_file, mock_print, mock_parse_args, mock_read_yaml):
        mock_parse_args.return_value = argparse.Namespace(
            op="Github1",
            func=form,
        )
        mock_read_yaml.return_value = {"required_fields": ["name", "age"]}
        main()
        mock_print.assert_not_called()  # assert that no errors were printed

    @patch("validation.read_yaml")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("builtins.print")
    def test_main_hostname(self, mock_print, mock_parse_args, mock_read_yaml):
        mock_parse_args.return_value = argparse.Namespace(
            instance="Github1",
            func=hostname,
        )
        mock_read_yaml.return_value = {
            "github_instances": [{"instance": "Github1", "url": "http://github1.com"}]
        }
        main()
        mock_print.assert_called_once_with("http://github1.com")


if __name__ == "__main__":
    unittest.main()
