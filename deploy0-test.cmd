@echo off
call .venv\Scripts\activate.bat
if "%~1"=="" (
    echo No deployment file specified. Using default: deploy.json
    set DEPLOY_FILE=deploy.json
) else (
    set DEPLOY_FILE=%~1
)
python ./src/deploy_4_developer/deploy.py --deploy ./%DEPLOY_FILE%
deactivate
