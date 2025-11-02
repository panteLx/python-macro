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
    pause
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
        pause
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
        pause
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

REM Deactivate when done
deactivate
