# -*- coding: utf-8 -*-
from collections import namedtuple
from typing import List, Union
import traceback
import paramiko
import time
import locale
import subprocess
from deploy_4_developer.cli.logger_init import get_logger

log = get_logger(name=__name__)

UploadFile = namedtuple("UploadFile", "source, target")


def ssh_action(
    host: str,
    port: int,
    username: str,
    password: str,
    actions: List[Union[str, UploadFile]],
    default_recv_length: int = 1024,
    recv_encode: str = "utf-8",
):
    """
    SSH Remote Operation Module
    :param host: The hostname or IP address of the remote server.
    :param port: the port number for SSH(default is 22,if not specified).
    :param username: The username for SSH authentication.
    :param password: The password for SSH authentication.
    :param actions: A list of actions to excute,which can be either command or file upload.
    :param default_recv_length: The default length for receiving data.
    :param recv_encode: The encoding to use for decoding received data.
    :return: None
    """

    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)

    def send_command(command: str):
        ssh_client = transport.open_session()
        ssh_client.set_combine_stderr(True)
        log.info(f"Starting to execute command: {command}")
        ssh_client.exec_command(command=command)
        while True:
            output = ssh_client.recv(default_recv_length)
            try:
                log.info(output.decode(recv_encode))
            except Exception as e:
                log.error("Error decoding received data.", exc_info=e)
            if ssh_client.exit_status_ready():
                break

    def send_file(upload_file: UploadFile):
        start_time = time.time()
        sftp = paramiko.SFTPClient.from_transport(transport)
        with open(upload_file.source, "rb") as fp:
            data = fp.read()
        log.info(
            f"Starting to upload file: {upload_file.source} to {upload_file.target}"
        )
        sftp.open(upload_file.target, "wb").write(data)
        log.info(
            f"File upload completed, time taken: {int(time.time() - start_time)} seconds"
        )

    try:
        for action in actions:
            if isinstance(action, str):
                send_command(action)
            elif isinstance(action, UploadFile):
                send_file(action)
            else:
                log.error(f"Unknown action type: {action} of type: {type(action)}")
    except Exception as e:
        log.error("An error occurred.", exc_info=True)
        raise e
    finally:
        transport.close()


def get_user_confirmation(message="Do you want to proceed? (y/n): "):
    """
    Ask the user for confirmation.
    :param message: The prompt message to display.
    :return: True if user confirms, False if denied.
    """
    while True:
        user_input = input(message).lower()
        if user_input == "y":
            return True
        elif user_input == "n":
            return False
        else:
            print('Invalid input. Please enter "y" or "n".')


def exec_local_cmd(cmd):
    """
    Execute a local system command and capture the output.
    :param cmd: Command to execute as a string.
    :return: None
    """
    try:
        log.info(f"Start executing command: {cmd}")
        response = subprocess.Popen(
            args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = (
            response.communicate()
        )  # Use communicate() to capture both stdout and stderr

        if stderr:
            log.error(
                f"Error executing command: {stderr.decode(locale.getpreferredencoding())}"
            )
        else:
            log.info(f"Command output: {stdout.decode(locale.getpreferredencoding())}")

    except subprocess.SubprocessError as e:
        log.error(f"Subprocess error occurred while executing {cmd}: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {traceback.format_exc()}")
    else:
        log.info(f"Command: {cmd} executed successfully.")


def exec_local_cmd_without_response(cmd):
    """
    Execute a local system command without capturing the output.
    :param cmd: Command to execute as a string.
    :return: None
    """
    try:
        log.info(f"Start executing command: {cmd}")
        subprocess.check_call(
            args=cmd, shell=True
        )  # Using check_call to raise an exception on failure
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed with return code {e.returncode}: {e}")
        raise e
    except Exception as e:
        log.error(f"An unexpected error occurred: {traceback.format_exc()}")
        raise e
    else:
        log.info(f"Command: {cmd} executed successfully.")
