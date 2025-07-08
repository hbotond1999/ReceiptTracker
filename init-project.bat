@echo off
setlocal enabledelayedexpansion
echo ===============================================
echo   ReceiptTracker Project Initialization
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Python is available
echo.

REM Check if virtual environment exists in root
if exist "venv\Scripts\activate.bat" (
    echo Found existing virtual environment
    call venv\Scripts\activate.bat
) else (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
    call venv\Scripts\activate.bat
)

echo.
echo Installing Python requirements...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Checking for .env file...
cd ..\docker

if not exist ".env" (
    echo Creating .env file...
    set /p openai_key="OpenAI API Key (leave empty for no AI): "

    copy .env.example .env >nul

    echo DATABASE_URL=postgresql://postgres:postgres@postgres:5432/receipt_tracker > .env
    echo ACCESS_TOKEN_EXPIRE_MINUTES=15 >> .env
    echo REFRESH_TOKEN_EXPIRE_DAYS=7 >> .env
    echo AI_MODEL=gpt-4.1 >> .env
    echo OPENAI_API_KEY=!openai_key! >> .env
    
    echo .env file created.
) else (
    echo .env file already exists - skipping configuration.
)

echo.
echo Generating RSA keys...
cd ..\backend
python generate_rsa_keys.py
if errorlevel 1 (
    echo ERROR: Failed to generate RSA keys
    pause
    exit /b 1
)

echo.
echo Copying RSA keys to docker directory...
if not exist "..\docker\backend\keys" mkdir "..\docker\backend\keys"
copy "keys\*" "..\docker\backend\keys\" /Y
if errorlevel 1 (
    echo ERROR: Failed to copy RSA keys
    pause
    exit /b 1
)

echo.
echo Starting Docker containers...
cd ..\docker
docker-compose up --build -d
if errorlevel 1 (
    echo ERROR: Failed to start Docker containers
    echo Make sure Docker is running and try again
    pause
    exit /b 1
)

echo.
echo Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo.
echo Reading DATABASE_URL from .env...
for /f "tokens=2 delims==" %%a in ('findstr "^DATABASE_URL=" .env') do set "database_url=%%a"
if "%database_url%"=="" (
    echo ERROR: DATABASE_URL not found in .env file
    pause
    exit /b 1
)
echo Docker Database URL: %database_url%

echo.
echo Converting database URL for local scripts (postgres to localhost)...
REM Convert Docker container name to localhost for Python scripts running on host
set "local_database_url=postgresql://postgres:postgres@localhost:5432/receipt_tracker"
echo Local Database URL: %local_database_url%

echo.
echo Initializing database...
python ..\backend\init_db.py "%local_database_url%"
if errorlevel 1 (
    echo ERROR: Failed to initialize database
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Setup completed successfully!
echo ===============================================
echo.
echo Application URLs:
echo - Frontend: http://localhost
echo - Backend API: http://localhost:8000
echo - Database: localhost:5432
echo.

set /p create_admin="Do you want to create an admin user now? (y/N): "
if /i "%create_admin%"=="y" (
    echo.
    echo Creating admin user...
    python ..\backend\create_admin.py "%local_database_url%"
    echo.
)

set /p generate_test="Do you want to generate test data? (y/N): "
if /i "%generate_test%"=="y" (
    echo.
    echo Generating test data...
    python ..\backend\generate_test_data.py "%local_database_url%"
    echo.
    echo Test data generated.
)

echo.
echo ===============================================
echo   Project initialization complete!
echo ===============================================
echo.
echo You can now access the application at:
echo - Frontend: http://localhost
echo - Backend API: http://localhost:8000
echo.
pause 