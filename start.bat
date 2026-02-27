@echo off
REM TaskManager - Windows Batch Startup Script
REM This script starts the Django development server

cls
echo.
echo ╔════════════════════════════════════════════╗
echo ║     TASKMANAGER - Windows Startup         ║
echo ║   Professional Task Management System     ║
echo ╚════════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo ✓ Virtual environment activated
echo.

REM Check database
if not exist "db.sqlite3" (
    echo Running database migrations...
    python manage.py migrate
    echo ✓ Database created
    echo.
)

REM Run migrations
echo Running migrations...
python manage.py migrate

echo.
echo Activating development server...
echo.
echo ════════════════════════════════════════════════════
echo ✓ Server is running on: http://localhost:8000
echo.
echo ✓ Login Credentials:
echo   Username: admin
echo   Password: admin@123
echo.
echo ✓ Press Ctrl+C to stop the server
echo ════════════════════════════════════════════════════
echo.

REM Start server
python manage.py runserver

pause
