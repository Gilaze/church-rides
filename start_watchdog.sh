#!/bin/bash
# Church Rides Watchdog Launcher for Linux/Mac
# Edit the variables below with your settings, then run: ./start_watchdog.sh

# ============ CONFIGURATION ============
# Replace these with your actual values:

export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password-here"
export ALERT_EMAIL="admin@example.com"
export WEBSITE_URL="https://your-app.leapcell.dev"

# Optional: Adjust check interval (in seconds)
export CHECK_INTERVAL=300

# If using production PostgreSQL database:
# export DATABASE_URL="postgresql://user:password@host:port/database"

# ========================================

echo "========================================"
echo "Church Rides Watchdog Service"
echo "========================================"
echo ""
echo "Starting watchdog with settings:"
echo "  Monitoring: $WEBSITE_URL"
echo "  Alert Email: $ALERT_EMAIL"
echo "  Check Interval: $CHECK_INTERVAL seconds"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

python3 watchdog.py
