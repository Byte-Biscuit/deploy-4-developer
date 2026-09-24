import argparse
import getpass
import json
import os
import sys

from deploy_4_developer.cli.logger_init import get_logger
from deploy_4_developer.cli.sys_util import (
    UploadFile,
    exec_local_cmd_without_response,
    ssh_action,
)

log = get_logger(name=__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="deploy4dev", description="Deploy Helper Tool"
    )
    parser.add_argument(
        "-d",
        "--deploy",
        metavar="deploy.json",
        default="deploy.json",
        type=str,
        required=False,
        help="Path to the deployment configuration file (default: %(default)s)",
    )
    args = parser.parse_args()

    # Set the deployment file name
    deploy_file_name = args.deploy
    if not deploy_file_name:
        deploy_file_name = "deploy.json"

    deploy_file = os.path.join(os.getcwd(), deploy_file_name)

    if not os.path.exists(deploy_file):
        log.info(f"Deployment file: {deploy_file} does not exist.")
        return 0

    log.info(f"Deploying using the configuration file: {deploy_file}")

    with open(file=deploy_file, mode="r", encoding="utf-8") as fp:
        deploy_json = json.load(fp)
        if not isinstance(deploy_json, dict):
            log.error("The deployment configuration file is not a valid JSON file.")
            return 1

    user = deploy_json.get("user")
    if not user:
        log.error("Missing 'user' key in the deployment configuration.")
        return 1
    host = deploy_json.get("host")
    if not host:
        log.error("Missing 'host' key in the deployment configuration.")
        return 1

    port = 22
    if "port" in deploy_json:
        raw_port = deploy_json["port"]
        if not isinstance(raw_port, int):
            log.error(f"Invalid 'port' value: {raw_port!r}")
            return 1
        port = raw_port

    # pre actions
    pre_actions = deploy_json.get("pre-actions")
    if pre_actions and len(pre_actions) > 0:
        try:
            for act in pre_actions:
                exec_local_cmd_without_response(act)
        except Exception:
            log.exception("Pre-actions failed.")
            return 1

    # actions
    json_actions = deploy_json.get("actions") or []
    actions = []
    for action in json_actions:
        if isinstance(action, str):
            actions.append(action)
        if isinstance(action, dict):
            action_type = action["type"]
            if "upload" == action_type:
                actions.append(UploadFile(source=action["from"], target=action["to"]))
    # Password must be provided either in the JSON file or via environment variable
    password = None
    if "password" in deploy_json:
        value = deploy_json["password"]
        if isinstance(value, str) and value.startswith("@env:"):
            var = value[5:]
            password = os.environ.get(var)
            if not password:
                log.error(f"Environment variable '{var}' is not set.")
                return 1
        elif isinstance(value, str):
            password = value

    # private key (optional)
    private_key_file = None
    private_key_pass = None
    if "private_key_file" in deploy_json:
        key_file = deploy_json["private_key_file"]
        if isinstance(key_file, str):
            private_key_file = key_file
        if "private_key_pass" in deploy_json:
            key_pass = deploy_json["private_key_pass"]
            if isinstance(key_pass, str) and key_pass.startswith("@env:"):
                var = key_pass[5:]
                private_key_pass = os.environ.get(var)
            elif isinstance(key_pass, str):
                private_key_pass = key_pass

    if not password and not private_key_file:
        password = getpass.getpass(prompt=f"Password for {user}@{host}: ")

    # Execute SSH actions if there are any
    if actions:
        log.info("Starting to execute SSH actions.")
        try:
            ssh_action(
                host=host,
                port=port,
                username=user,
                password=password,
                private_key_file=private_key_file,
                private_key_pass=private_key_pass,
                actions=actions,
            )
        except Exception:
            log.exception("SSH actions failed.")
            return 1

    # post actions
    post_actions = deploy_json.get("post-actions")
    if post_actions and len(post_actions) > 0:
        try:
            for act in post_actions:
                exec_local_cmd_without_response(act)
        except Exception:
            log.exception("Post-actions failed.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
