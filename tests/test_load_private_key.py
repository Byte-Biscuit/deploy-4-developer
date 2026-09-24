import subprocess
from pathlib import Path

import paramiko
import pytest

from deploy_4_developer.cli.sys_util import load_private_key


def _ssh_keygen(key_path: Path, key_type: str) -> None:
    subprocess.run(
        [
            "ssh-keygen",
            "-t",
            key_type,
            "-f",
            str(key_path),
            "-N",
            "",
            "-q",
        ],
        check=True,
    )


@pytest.mark.parametrize(
    "key_type,expected_cls",
    [
        ("rsa", paramiko.RSAKey),
        ("ed25519", paramiko.Ed25519Key),
        ("ecdsa", paramiko.ECDSAKey),
    ],
)
def test_load_private_key_supported_algorithms(tmp_path, key_type, expected_cls):
    key_path = tmp_path / f"id_{key_type}"
    _ssh_keygen(key_path, key_type)

    pkey = load_private_key(str(key_path))
    assert isinstance(pkey, expected_cls)


def test_load_private_key_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(Exception):
        load_private_key(str(missing))
