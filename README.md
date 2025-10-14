# deploy-4-developer

[简体中文](README.zh-CN.md)

`deploy-4-developer` is a lightweight deployment automation tool designed for developers. It reads a structured `deploy.json` configuration file to help you upload local build artifacts to a remote host, execute commands on the remote host, and perform local cleanup tasks—simplifying deployments for development and test environments.

This document targets first-time users and covers installation, quick start, configuration format, and common troubleshooting.

## Installation

Install the package from PyPI:

```powershell
# Install from PyPI (recommended)
pip install deploy-4-developer
```

After installation, the package will install a console script into the current Python interpreter's scripts directory (example name: `deploy4dev`, defined by `project.scripts` in `pyproject.toml`).

Notes:

-   If you install inside a virtual environment and activate it, the console script will be available in the activated environment:

```powershell
# Activate (example) - PowerShell
.\.venv\Scripts\Activate.ps1
deploy4dev -d deploy.json
```

-   If you installed for your user or system but `deploy4dev` is not in your global PATH, here is how to locate and temporarily add the scripts directory to PATH (PowerShell example):

Temporarily add the scripts directory to the current PowerShell session PATH (lost after restarting the shell):

```powershell
$scripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$env:Path += ";$scripts"
# Now run
deploy4dev -d deploy.json
```

Permanently add the scripts directory to the current user's PATH (writes to user environment variables):

```powershell
[Environment]::SetEnvironmentVariable('Path', $env:Path + ';' + (python -c "import sysconfig; print(sysconfig.get_path('scripts'))"), 'User')
# You may need to restart the terminal or re-login for changes to take effect
```

Verify installation:

```powershell
Get-Command deploy4dev -ErrorAction SilentlyContinue
# or (on systems with which)
which deploy4dev
```

If these commands return a path, `deploy4dev` is installed correctly and can be run from any shell.

## Quick Start

### Sample configuration

```json
{
    "host": "hostname or ip",
    "user": "user",
    "port": 22,
    "password": "@env:env_name",
    "private_key_file": "/path/to/private/key",
    "private_key_pass": "@env:env_name",
    "pre-actions": [
        "tarz  -i deployment service namespace serviceaccount ingress example-component"
    ],
    "actions": [
        "mv /remote/path/app /remote/path/app_`date +%Y%m%d%H%M%S` ",
        {
            "type": "upload",
            "from": "C:\\path\\to\\app.tar.gz",
            "to": "/remote/path/app.tar.gz"
        },
        "mkdir -p /remote/path/app",
        "tar -zxvf /remote/path/app.tar.gz -C /remote/path/app",
        "rm -f /remote/path/app.tar.gz",
        "kubectl apply -f /remote/path/app/deployment.yaml",
        "kubectl rollout restart deployment.apps/example-deployment"
    ],
    "post-actions": ["del /f C:\\path\\to\\app.tar.gz"]
}
```

About the `password` field:

-   You may omit the `password` field in `deploy.json` (recommended for interactive or local runs). If the configuration file does not include a password, the CLI will prompt you to enter one at runtime (input is hidden).
-   If you want to reference a password from the environment, use the environment placeholder form, for example `"password": "@env:env_name"`. The program will read the value from the operating system environment variable `env_name`. Do not store plain-text passwords in the configuration file.

### Private key authentication

deploy4dev also supports authenticating with an SSH private key instead of a password. To use a private key, add the optional `private_key_file` field to your configuration. Example (Windows path):

```json
{
    "host": "example.com",
    "user": "deploy",
    "private_key_file": "C:\\Users\\you\\.ssh\\id_rsa"
}
```

On Unix-like systems use a POSIX path, for example:

```json
{
    "host": "example.com",
    "user": "deploy",
    "private_key_file": "/home/ci/.ssh/id_rsa"
}
```

Notes:

-   If `private_key_file` is present, `password` is usually not required. If the private key is protected by a passphrase, you can provide the passphrase with the optional `private_key_pass` field, or use an SSH agent (ssh-agent, Pageant, or similar). Example:

```json
{
    "host": "example.com",
    "user": "deploy",
    "private_key_file": "/home/ci/.ssh/id_rsa",
    "private_key_pass": "@env:KEY_PASSPHRASE"
}
```

-   File access details: ensure the process running `deploy4dev` can read the key file; no lengthy discussion of filesystem ACLs is necessary here — keep keys protected as appropriate for your environment.
-   Alternatively, load the key into an SSH agent before running `deploy4dev` and omit both `private_key_file` and `private_key_pass` from the config.

### JSON trailing-comma warning

JSON strictly forbids trailing commas in arrays and objects. A very common source of parse errors is leaving a comma after the last element. For example, this is invalid and will fail to parse:

```json
"actions": [
    "cmd1",
    "cmd2",
]
```

The correct form (no trailing comma) is:

```json
"actions": [
    "cmd1",
    "cmd2"
]
```

Ways to validate your JSON before running:

-   Use Python's JSON tool: `python -m json.tool deploy.json` (this will print a formatted JSON or error on invalid input).
-   In PowerShell: `Get-Content deploy.json -Raw | ConvertFrom-Json`.

If you get a JSON parse error while running `deploy4dev`, check for trailing commas or use one of the validators above.

### Start a deployment

```powershell
# This will read deploy.json in the current directory and start the deployment
deploy4dev
# You can specify another config file with -d (default is deploy.json). Example:
deploy4dev -d deploy-staging.json
```

## Logs & Troubleshooting

-   Common failures: remote SSH not running, unreachable host, environment variables not injected, incorrect file paths, or permission issues.
-   Upload failures: verify the local file path and remote directory permissions.
-   Remote commands produce no output or fail: break the steps down in `deploy.json` and test each command directly on the remote host.

## Developer Notes & Contributing

-   Source code location: `src/deploy_4_developer/cli`.
-   Local development suggestions:

```powershell
git clone git@github.com:Byte-Biscuit/deploy-4-developer.git
# Change to project directory
cd deploy-4-developer
# The project uses uv for build management; make sure your uv environment is ready
uv sync
```

-   Contributions via issues and pull requests are welcome.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
