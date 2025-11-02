@echo off
echo ========================================
echo   MacroManager
echo ========================================
echo.

REM Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    echo.
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Python is not installed!`n`nPlease install Python 3.8 or higher from https://www.python.org/downloads/', 'MacroManager - Error', 'OK', 'Error')"
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Setting up for the first time...
    echo.
    
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Failed to create virtual environment.`n`nPlease check your Python installation and permissions.', 'MacroManager - Error', 'OK', 'Error')"
        exit /b 1
    )
    echo Virtual environment created!
    echo.
    
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies.
        powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Failed to install dependencies.`n`nPlease check your internet connection and requirements.txt file.', 'MacroManager - Error', 'OK', 'Error')"
        exit /b 1
    )
    
    echo.
    echo Setup complete!
    echo.
) else (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Add src directory to Python path
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Start the application
echo Starting MacroManager...
echo.
python main.py

if %errorlevel% neq 0 (
    echo ERROR: MacroManager failed to start.
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('MacroManager failed to start.`n`nExit code: %errorlevel%`n`nPlease check the console output above for more details.', 'MacroManager - Error', 'OK', 'Error')"
    pause
    exit /b %errorlevel%
)

REM Deactivate when done
deactivate
