@echo off
REM Church Rides Watchdog Launcher for Windows
REM Edit the variables below with your settings, then double-click this file to run

REM ============ CONFIGURATION ============
REM Replace these with your actual values:

set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password-here
set ALERT_EMAIL=admin@example.com
set WEBSITE_URL=https://your-app.leapcell.dev

REM Optional: Adjust check interval (in seconds)
set CHECK_INTERVAL=300

REM If using production PostgreSQL database:
REM set DATABASE_URL=postgresql://user:password@host:port/database

REM ========================================

echo ========================================
echo Church Rides Watchdog Service
echo ========================================
echo.
echo Starting watchdog with settings:
echo   Monitoring: %WEBSITE_URL%
echo   Alert Email: %ALERT_EMAIL%
echo   Check Interval: %CHECK_INTERVAL% seconds
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python watchdog.py

pause
