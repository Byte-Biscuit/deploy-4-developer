# -*- coding: utf-8 -*-
import logging
import argparse
import getpass
import json
import os
from deploy_4_developer.sys_util import ssh_action, UploadFile, exec_local_cmd_without_response

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Deploy Helper Tool')
    parser.add_argument('--deploy', '-d', default="deploy.json", type=str, required=False,
                        help='Path to the deployment configuration file')
    args = parser.parse_args()

    # Set the deployment file name
    deploy_file_name = args.deploy
    if not deploy_file_name:
        deploy_file_name = "deploy.json"

    deploy_file = os.path.join(os.getcwd(), deploy_file_name)

    if not os.path.exists(deploy_file):
        log.info(f"Deployment file: {deploy_file} does not exist.")
        exit(0)

    log.info(f"Deploying using the configuration file: {deploy_file}")

    with open(file=deploy_file, mode="r", encoding="utf-8") as fp:
        deploy_json = json.load(fp)
        if not isinstance(deploy_json, dict):
            log.error("The deployment configuration file is not a valid JSON file.")
            exit(1)

    user = deploy_json.get("user")
    if not user:
        log.error("Missing 'user' key in the deployment configuration.")
        exit(1)
    host = deploy_json.get("host")
    if not host:
        log.error("Missing 'host' key in the deployment configuration.")
        exit(1)

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
            exit(1)

    # actions
    json_actions = deploy_json.get("actions")
    actions = []
    for action in json_actions:
        if isinstance(action, str):
            actions.append(action)
        if isinstance(action, dict):
            action_type = action["type"]
            if "upload" == action_type:
                actions.append(UploadFile(
                    source=action["from"],
                    target=action["to"]))

    if "password" in deploy_json:
        password = deploy_json.get("password")
    else:
        password = getpass.getpass(f"User [{user}] please enter your password: ")

    # Execute SSH actions if there are any
    if actions:
        log.info("Starting to execute SSH actions.")
        try:
            ssh_action(host=host, port=port, username=user, password=password, actions=actions)
        except:
            exit(1)

    # post actions
    post_actions = deploy_json.get("post-actions")
    if post_actions and len(post_actions) > 0:
        try:
            for act in post_actions:
                exec_local_cmd_without_response(act)
        except:
            exit(1)


if __name__ == '__main__':
    main()
