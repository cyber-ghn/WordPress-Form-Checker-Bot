@echo off
rem --- retrieve the path of the current script ---
set "SCRIPT_DIR=%~dp0"

rem --- check if Python 3.10.11 is installed ---
echo Checking for Python 3.10.11 installation
py -0p | findstr /R /C:"3\.10" >nul
if %errorlevel%==0 (
    for /f "usebackq tokens=2" %%i in (`py -0p ^| findstr /R /C:"3\.10"`) do set "PYTHON_PATH=%%i"
) else (
    echo Python 3.10 is not installed. Please install Python 3.10.11 from https://www.python.org/downloads/release/python-31011/
    exit /b 1
)

rem --- create and activate virtual environment ---
"%PYTHON_PATH%" -m venv "%SCRIPT_DIR%.venv"
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"

rem --- upgrade pip ---
python -m pip install --upgrade pip

rem --- install required packages ---
python -m pip install -r "%SCRIPT_DIR%src\requirements.txt"

echo Setup complete.

rem --- run the python script once ---
python "%SCRIPT_DIR%src\bot_orchestrator.py"

echo Setup done successfully.
