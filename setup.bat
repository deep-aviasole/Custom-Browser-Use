@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo           Starting setup...
echo ========================================
echo.

REM === Settings ===
set "UV_INSTALL_DIR=%USERPROFILE%\.local\bin"
set "UV_EXE=%UV_INSTALL_DIR%\uv.exe"
set "VENV_DIR=.venv"
set "UV_URL=https://astral.sh/uv/install.ps1"

REM === STEP 1: Download uv if not present ===
echo [STEP 1] Checking for uv.exe...
if not exist "%UV_EXE%" (
    echo [INFO] uv.exe not found in %UV_INSTALL_DIR%. Installing via PowerShell...
    powershell -ExecutionPolicy Bypass -Command "iwr %UV_URL% -useb | iex"

    if not exist "%UV_EXE%" (
        echo [ERROR] uv.exe failed to install at expected path: %UV_EXE%
        echo [HINT] Try running 'uv' manually from PowerShell and check if it's globally installed.
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] uv.exe installed successfully at %UV_EXE%
    )
) else (
    echo [INFO] uv.exe already exists.
)

echo.

REM === STEP 2: Check for .env and requirements.txt ===
echo [STEP 2] Checking for .env and requirements.txt...

if exist "./web-ui/requirements.txt" (
    echo [INFO] Found requirements.txt.
) else (
    echo [ERROR] requirements.txt not found. Cannot continue.
    pause
    exit /b 1
)

if exist ".env" (
    echo [INFO] Found .env file. Copying to web-ui/.env...
    copy /Y ".env" "web-ui\.env" >nul
    if exist "web-ui\.env" (
        echo [SUCCESS] web-ui/.env updated with .env content.
    ) else (
        echo [ERROR] Failed to copy .env to web-ui/.env.
        pause
        exit /b 1
    )
) else (
    echo [WARNING] .env file not found. web-ui/.env will not be updated.
)

echo.

REM === STEP 3: Create virtual environment ===
echo [STEP 3] Creating virtual environment using uv...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    "%UV_EXE%" venv %VENV_DIR%
    if exist "%VENV_DIR%\Scripts\activate.bat" (
        echo [SUCCESS] Virtual environment created.
    ) else (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment already exists.
)

echo.

REM === STEP 4: Activate venv ===
echo [STEP 4] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
) else (
    echo [SUCCESS] Virtual environment activated.
)

echo.

REM === STEP 5: Install dependencies ===
echo [STEP 5] Checking and installing dependencies...
"%UV_EXE%" pip install -r web-ui/requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
) else (
    echo [SUCCESS] Dependencies installed successfully.
)

echo.

REM === STEP 6: Ensure Playwright is installed ===
echo [STEP 6] Ensuring Playwright and browsers are installed...

"%UV_EXE%" pip install playwright
if errorlevel 1 (
    echo [ERROR] Failed to install Playwright package.
    pause
    exit /b 1
) else (
    echo [INFO] Playwright package installed.
)

"%VENV_DIR%\Scripts\python.exe" -m playwright install
if errorlevel 1 (
    echo [ERROR] Playwright browser install failed.
    pause
    exit /b 1
) else (
    echo [SUCCESS] Playwright browsers installed.
)

echo.
if exist "web-ui\link.txt" del "web-ui\link.txt"

REM === STEP 7: Run your app ===
echo [STEP 7] Launching your application...
REM Run Python app in background
start "" /MIN cmd /c python web-ui/webui.py

REM Wait for link.txt
:wait_loop
if exist "web-ui\link.txt" (
    set /p URL=<web-ui\link.txt
    if defined URL (
        echo [DEBUG] URL is: [!URL!]
        echo [INFO] Opening !URL! in browser...
        start "" "!URL!"
        goto continue_script
    )
)
timeout /t 3 >nul
goto wait_loop

:continue_script

echo.

echo ========================================
echo                Finished.
echo ========================================

REM === Keep console open ===
echo [INFO] The application is running. Press any key to stop.
