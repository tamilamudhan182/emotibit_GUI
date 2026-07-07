@echo off
echo ====================================================
echo EmotiBit - Signal Quality Control Environment Setup
echo ====================================================
echo.

:: 1. Check if uv is installed, if not, install it using PowerShell
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] uv package manager is not installed. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
) else (
    echo [INFO] uv is already installed.
)

:: 2. Identify the absolute path to uv.exe
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_PATH=%USERPROFILE%\.local\bin\uv.exe"
) else (
    set "UV_PATH=uv"
)

echo.
echo [INFO] Creating Python 3.11 virtual environment in .venv_sqi...
"%UV_PATH%" venv .venv_sqi --python 3.11 --clear
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b %errorlevel%
)

echo.
echo [INFO] Installing vital_sqi dependencies from requirements_sqi.txt...
"%UV_PATH%" pip install -r requirements_sqi.txt --python .venv_sqi
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo.
echo ====================================================
echo [SUCCESS] Environment successfully set up at .venv_sqi!
echo You can now run your quality check scripts using:
echo .venv_sqi\Scripts\python.exe ^<your_script.py^>
echo ====================================================
echo.
pause
