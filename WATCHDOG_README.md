# Church Rides Watchdog Service 🔍

A standalone monitoring service that watches your Church Rides website and sends email alerts when the service goes down, including all current ride assignments and passenger information.

## Features

- ✅ **Automatic Monitoring**: Checks your website at regular intervals
- 📧 **Email Alerts**: Sends detailed alerts when the service is down
- 🚗 **Ride Data Backup**: Includes all vehicles and passengers in alert emails
- 🔄 **Recovery Notifications**: Alerts you when the service comes back online
- ⏱️ **Configurable Intervals**: Set your own check frequency
- 🛡️ **Smart Alerting**: Cooldown period prevents alert spam
- 🔌 **Independent**: Runs separately from your Flask app

## How It Works

1. **Periodic Health Checks**: The watchdog makes HTTP requests to your website every X seconds (configurable)
2. **Failure Detection**: If the website doesn't respond or returns an error, it counts as a failure
3. **Threshold Trigger**: After N consecutive failures (default: 2), it triggers an alert
4. **Database Query**: Retrieves all current rides and passengers from the database
5. **Email Alert**: Sends a detailed email with all ride information
6. **Recovery Detection**: Monitors for recovery and sends a notification when service is restored

## Setup Instructions

### 1. Install Required Dependencies

The watchdog needs the `requests` library for HTTP checks:

```bash
pip install requests
```

### 2. Configure Email Settings

#### Option A: Using Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Church Rides Watchdog"
   - Copy the 16-character password

3. **Set Environment Variables**:

**Windows (Command Prompt):**
```cmd
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-16-char-app-password
set ALERT_EMAIL=admin@example.com
set WEBSITE_URL=https://your-app.leapcell.dev
```

**Windows (PowerShell):**
```powershell
$env:SMTP_USERNAME="your-email@gmail.com"
$env:SMTP_PASSWORD="your-16-char-app-password"
$env:ALERT_EMAIL="admin@example.com"
$env:WEBSITE_URL="https://your-app.leapcell.dev"
```

**Linux/Mac:**
```bash
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-16-char-app-password
export ALERT_EMAIL=admin@example.com
export WEBSITE_URL=https://your-app.leapcell.dev
```

#### Option B: Using .env File

1. Copy the example config:
```bash
cp .env.watchdog.example .env.watchdog
```

2. Edit `.env.watchdog` with your settings

3. Load it before running:
```bash
# Install python-dotenv
pip install python-dotenv

# Modify watchdog.py to load it (add at top):
from dotenv import load_dotenv
load_dotenv('.env.watchdog')
```

### 3. Configure Database Connection

The watchdog uses the same `db.py` file as your Flask app.

**For Production (PostgreSQL):**
```bash
set DATABASE_URL=postgresql://user:password@host:port/database
```

**For Local Testing (SQLite):**
No configuration needed - it will use `church_ride.db` by default.

### 4. Test the Watchdog

Run the watchdog once to test:

```bash
python watchdog.py
```

You should see output like:
```
[2024-01-15 14:30:00] Church Rides Watchdog Service started
Monitoring: https://your-app.leapcell.dev
Check interval: 300 seconds
Failure threshold: 2
Alert email: admin@example.com
------------------------------------------------------------
[2024-01-15 14:30:05] ✓ Website is healthy
```

Press `Ctrl+C` to stop.

## Running the Watchdog

### Method 1: Run Continuously in Terminal

Simple but stops when you close the terminal:

```bash
python watchdog.py
```

### Method 2: Windows Task Scheduler (Recommended for Windows)

1. **Open Task Scheduler**
2. **Create Basic Task**:
   - Name: "Church Rides Watchdog"
   - Trigger: "When I log on"
   - Action: "Start a program"
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `C:\Users\Ethan\OneDrive\Desktop\church-rides\watchdog.py`
   - Start in: `C:\Users\Ethan\OneDrive\Desktop\church-rides`
3. **Set to run even when not logged in** (optional)

### Method 3: Linux Cron Job

Create a script to run the watchdog:

**create `start_watchdog.sh`:**
```bash
#!/bin/bash
cd /path/to/church-rides
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export ALERT_EMAIL=admin@example.com
export WEBSITE_URL=https://your-app.leapcell.dev
python3 watchdog.py
```

**Make it executable:**
```bash
chmod +x start_watchdog.sh
```

**Add to crontab to run at boot:**
```bash
crontab -e
# Add this line:
@reboot /path/to/church-rides/start_watchdog.sh >> /path/to/watchdog.log 2>&1
```

### Method 4: Systemd Service (Linux)

Create `/etc/systemd/system/church-rides-watchdog.service`:

```ini
[Unit]
Description=Church Rides Watchdog Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/church-rides
Environment="SMTP_USERNAME=your-email@gmail.com"
Environment="SMTP_PASSWORD=your-app-password"
Environment="ALERT_EMAIL=admin@example.com"
Environment="WEBSITE_URL=https://your-app.leapcell.dev"
ExecStart=/usr/bin/python3 watchdog.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable church-rides-watchdog
sudo systemctl start church-rides-watchdog
sudo systemctl status church-rides-watchdog
```

### Method 5: Cloud Hosting (Best for Production)

Deploy the watchdog to a separate cloud service:

**Free Options:**
- **PythonAnywhere**: Free tier includes scheduled tasks
- **Railway**: Free tier with always-on services
- **Render**: Free tier with background workers
- **Fly.io**: Free tier with background processes

## Configuration Options

Edit the top of `watchdog.py` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSITE_URL` | - | Your website to monitor |
| `CHECK_INTERVAL` | 300 | Seconds between checks (300 = 5 min) |
| `SMTP_SERVER` | smtp.gmail.com | Email server address |
| `SMTP_PORT` | 587 | Email server port |
| `SMTP_USERNAME` | - | Your email address |
| `SMTP_PASSWORD` | - | Your email password/app password |
| `ALERT_EMAIL` | - | Where to send alerts |
| `REQUEST_TIMEOUT` | 10 | Seconds to wait for response |
| `FAILURE_THRESHOLD` | 2 | Failures before alerting |

## Email Alert Contents

When the service goes down, you'll receive an email with:

- ⏰ **Time of alert**
- 🔢 **Number of consecutive failures**
- 🚗 **All vehicles** with driver info
- 👥 **All passengers** for each vehicle
- 📞 **Contact information** (phone numbers)
- 📊 **Capacity information** for each vehicle

Example alert:
```
ALERT: Church Rides Service is DOWN

The church rides website (https://your-app.leapcell.dev) is currently not responding.

Time of Alert: 2024-01-15 14:35:00
Consecutive Failures: 2

Current Ride Assignments:
============================================================
CURRENT RIDE ASSIGNMENTS
============================================================

Vehicle: Blue Honda Civic
Driver: John Doe
Driver Phone: (555) 123-4567
Capacity: 3/4

Passengers:
  1. Jane Smith (Sophomore) - (555) 234-5678
  2. Bob Johnson (Junior) - (555) 345-6789
  3. Alice Williams (Freshman) - (555) 456-7890

------------------------------------------------------------
```

## Troubleshooting

### "Error sending email: Authentication failed"
- Check your SMTP username and password
- For Gmail, make sure you're using an App Password, not your regular password
- Verify 2FA is enabled on your Gmail account

### "Connection error - website may be down"
- Verify the WEBSITE_URL is correct
- Check if your website is actually accessible
- Check your internet connection

### "Error retrieving ride data from database"
- Verify DATABASE_URL is set correctly for production
- Check database permissions
- Make sure `db.py` is in the same directory

### Watchdog stops running
- Use Task Scheduler (Windows) or systemd (Linux) for automatic restarts
- Check logs for error messages
- Ensure your computer/server doesn't go to sleep

### Too many alert emails
- Increase `FAILURE_THRESHOLD` (requires more consecutive failures)
- Increase `CHECK_INTERVAL` (checks less frequently)
- The watchdog has a 1-hour cooldown between alerts by default

## Best Practices

1. **Test First**: Run manually to verify email sending works
2. **Set Realistic Intervals**: 5-10 minutes is usually sufficient
3. **Monitor the Monitor**: Set up the watchdog on a different server than your app
4. **Keep Credentials Safe**: Use environment variables, never commit passwords
5. **Check Your Email Limits**: Gmail has sending limits (500/day for free accounts)

## Security Notes

- ⚠️ Never commit your `.env.watchdog` file with real credentials
- Use App Passwords instead of your main email password
- The watchdog only reads from the database, never writes
- Consider using a dedicated email account for monitoring

## Need Help?

- Check the logs for error messages
- Verify all environment variables are set correctly
- Test email sending separately using a simple Python script
- Make sure `db.py` and the database are accessible

---

**Happy Monitoring! 🎉**
