# -*- coding: utf-8 -*-
from collections import namedtuple
from typing import List, Union
from pathlib import Path
import traceback
import codecs
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
    username: str = None,
    password: str = None,
    private_key_file: str = None,
    private_key_pass: str = None,
    actions: List[Union[str, UploadFile]] = None,
    default_recv_length: int = 1024,
    recv_encode: str = "utf-8",
):
    """
    SSH remote operation helper.

    Parameters:
        host (str): Hostname or IP address of the remote server.
        port (int): SSH port number (commonly 22).
        username (str, optional): Username for SSH authentication.
        password (str, optional): Password for SSH authentication (ignored if private_key is used).
        private_key_file (Path, optional): Path to a private key file for key-based authentication.
        private_key_pass (str, optional): Passphrase for the private key if it is encrypted.
        actions (List[Union[str, UploadFile]], optional): List of actions to execute. Each action is either
            a shell command string or an UploadFile(namedtuple) for uploads.
        default_recv_length (int, optional): Number of bytes to read per recv call (default: 1024).
        recv_encode (str, optional): Encoding used to decode received byte data (default: "utf-8").

    Returns:
        None
    """
    if not actions:
        log.error("No actions to perform.")
        return
    transport = paramiko.Transport((host, port))
    if private_key_file:
        pkey = paramiko.RSAKey.from_private_key_file(
            filename=private_key_file, password=private_key_pass
        )
        transport.connect(username=username, pkey=pkey)
    else:
        transport.connect(username=username, password=password)

    def send_command(command: str):
        ssh_client = transport.open_session()
        ssh_client.set_combine_stderr(True)
        log.info(f"Starting to execute command: {command}")
        ssh_client.exec_command(command=command)

        # 增量解码器，避免多字节序列在 chunk 边界解码失败
        decoder = codecs.getincrementaldecoder(recv_encode)()
        try:
            while True:
                # 优先通过 recv_ready 避免阻塞/空读取
                if ssh_client.recv_ready():
                    chunk = ssh_client.recv(default_recv_length)
                    if not chunk:
                        break

                    # 简单二进制判定（包含 NUL 或大量非文本字节）
                    if b"\x00" in chunk or sum(
                        1 for b in chunk if b < 9 or (b > 13 and b < 32)
                    ) > (len(chunk) * 0.3):
                        # 可能是二进制（tar/gzip 等），写入文件或以 latin-1 直通记录
                        log.info("[binary data chunk] (length=%d)" % len(chunk))
                        # 若需要，把二进制保存到文件而不是 decode
                        # with open("remote_output.bin", "ab") as f: f.write(chunk)
                        continue

                    # 尝试增量解码，失败时用替代策略
                    try:
                        text = decoder.decode(chunk)
                    except UnicodeDecodeError:
                        text = chunk.decode(recv_encode, errors="replace")
                        log.debug("Fallback decoding used for chunk (errors=replace).")
                    log.info(text)

                else:
                    # 避免忙等
                    time.sleep(0.05)

                if ssh_client.exit_status_ready():
                    # flush 剩余 bytes
                    try:
                        rest = decoder.decode(b"", final=True)
                        if rest:
                            log.info(rest)
                    except Exception:
                        pass
                    break
        except Exception as e:
            log.error("Error reading from SSH channel.", exc_info=e)
        """
        while True:
            output = ssh_client.recv(default_recv_length)
            try:
                log.info(output.decode(recv_encode))
            except Exception as e:
                log.error("Error decoding received data.", exc_info=e)
            if ssh_client.exit_status_ready():
                break
        """

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
