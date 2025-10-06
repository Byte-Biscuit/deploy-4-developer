# -*- coding: utf-8 -*-
import logging
import sys
import argparse
import getpass
import json
import os
from deploy_4_developer.cli.sys_util import (
    ssh_action,
    UploadFile,
    exec_local_cmd_without_response,
)
from deploy_4_developer.cli.logger_init import get_logger

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
        port = deploy_json.get("port")

    # pre actions
    pre_actions = deploy_json.get("pre-actions")
    if pre_actions and len(pre_actions) > 0:
        try:
            for act in pre_actions:
                exec_local_cmd_without_response(act)
        except:
            return 1

    # actions
    json_actions = deploy_json.get("actions")
    actions = []
    for action in json_actions:
        if isinstance(action, str):
            actions.append(action)
        if isinstance(action, dict):
            action_type = action["type"]
            if "upload" == action_type:
                actions.append(UploadFile(source=action["from"], target=action["to"]))
    # Password must be provided either in the JSON file or via environment variable
    if "password" in deploy_json:
        value = deploy_json.get("password")
        if value.startswith("@env:"):
            var = value[5:]
            password = os.environ.get(var)
            if not password:
                log.error(f"Environment variable '{var}' is not set.")
                return 1
    else:
        password = getpass.getpass(f"User [{user}] please enter your password: ")

    # Execute SSH actions if there are any
    if actions:
        log.info("Starting to execute SSH actions.")
        try:
            ssh_action(
                host=host, port=port, username=user, password=password, actions=actions
            )
        except:
            return 1

    # post actions
    post_actions = deploy_json.get("post-actions")
    if post_actions and len(post_actions) > 0:
        try:
            for act in post_actions:
                exec_local_cmd_without_response(act)
        except:
            return 1


if __name__ == "__main__":
    sys.exit(main())
