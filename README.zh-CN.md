# deploy-4-developer

[English / English version: README.md]

`deploy-4-developer` 是为开发者设计的轻量级部署自动化工具。它通过读取一个结构化的 `deploy.json` 配置文件，帮助你把本地构建产物上传到远端主机、在远端执行命令、以及在本地做收尾清理等常见部署操作，从而简化开发/测试环境的部署流程并提升效率。

以下文档面向第一次使用的开发者，涵盖安装、快速开始、配置格式与常见问题。

## 安装

你可以直接从 PyPI 安装发布包：

```powershell
# 直接从 PyPI 安装（推荐）
pip install deploy-4-developer
```

安装后，包会在当前 Python 解释器的 scripts 目录中创建可执行脚本（示例名：`deploy4dev`，由 `pyproject.toml` 的 `project.scripts` 定义）。

注意：

-   如果你在虚拟环境中安装并激活虚拟环境，可执行命令会自动在激活的环境中可用：

```powershell
# 激活（示例）,PowerShell
.\.venv\Scripts\Activate.ps1
deploy4dev -d deploy.json
```

-   如果你做的是用户安装或系统安装，但 `deploy4dev` 未在全局 PATH 中，下面是检查与把脚本目录加入 PATH 的方法（PowerShell 示例）：

临时把 scripts 目录加入当前 PowerShell 会话的 PATH（重启终端后失效）：

```powershell

$scripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$env:Path += ";$scripts"
# 现在可运行
deploy4dev -d deploy.json
```

将 scripts 目录永久加入当前用户的 PATH（写入用户环境变量）：

````powershell
```powershell
[Environment]::SetEnvironmentVariable('Path', $env:Path + ';' + (python -c "import sysconfig; print(sysconfig.get_path('scripts'))"), 'User')
# 修改生效可能需要重启终端或重新登录
````

校验安装：

```powershell
Get-Command deploy4dev -ErrorAction SilentlyContinue
# 或者
which deploy4dev
```

如果上面命令能返回路径，说明 `deploy4dev` 已正确加入 PATH，并可在任意命令行目录直接运行。

## 快速开始

### 配置样例

```json
{
    "host": "hostname or ip",
    "user": "user",
    "password": "@env:env_name",
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

关于 `password` 字段说明：

-   你可以在 `deploy.json` 中不配置 `password` 字段（推荐在交互式或本地临时运行时省略）。如果配置文件中未包含密码，CLI 会在运行时提示你输入密码（隐藏回显）。
-   如果你希望在配置文件中指定一个引用，请使用环境变量占位形式，例如 `"password": "@env:env_name"`；程序会从操作系统环境变量 `env_name` 中读取值。请不要将明文密码写入配置文件。

### 开始部署

```powershell
# 将会开始读取当前目录下的deploy.json文件,执行部署操作
deploy4dev
# 你可以使用 `-d` 指定其他配置文件名（默认会寻找 `deploy.json`）。例如如果你有多个环境配置
deploy4dev -d deploy-staging.json
```

## 日志与故障排查

-   常见失败原因：远端 SSH 未启动、主机不可达、环境变量未注入、文件路径错误或权限不足。
-   上传失败：检查本地文件路径是否正确、远端目标目录权限。
-   远端命令无输出或失败：在 `deploy.json` 中逐步拆分并单独在远端测试命令。

## 开发者说明与贡献

-   源代码位置：`src/deploy_4_developer/cli`。
-   本地开发建议：

```powershell
git clone git@github.com:Byte-Biscuit/deploy-4-developer.git
# 切换到项目目录
cd deploy-4-developer
# 项目使用rye进行构建管理,请预先配置好rye环境
rye sync
```

-   欢迎通过 issue/PR 提交功能改进。

## 授权

本项目采用 MIT License，详见 `LICENSE` 文件。
