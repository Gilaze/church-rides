# Integrated Watchdog Monitoring (APScheduler)

## Overview

The watchdog monitoring is now **integrated directly into your Flask app** using APScheduler. This means:

✅ **No separate worker process needed**
✅ **Runs automatically when your web app starts**
✅ **Uses async background tasks**
✅ **Simpler deployment on Leapcell**
✅ **Single service, single Procfile**

## How It Works

```
┌─────────────────────────────────────────────────────┐
│         Your Flask App (Single Service)            │
│                                                     │
│  ┌──────────────┐         ┌───────────────────┐   │
│  │  Web Server  │         │  APScheduler      │   │
│  │  (Gunicorn)  │         │  Background Tasks │   │
│  │              │         │                   │   │
│  │  Handles     │         │  Every 5 minutes: │   │
│  │  HTTP        │         │  - Check website  │   │
│  │  requests    │         │  - Send alerts    │   │
│  └──────────────┘         └───────────────────┘   │
│                                                     │
│  Both run in the same process!                     │
└─────────────────────────────────────────────────────┘
```

## Files Created

1. **`watchdog_scheduler.py`** - Background monitoring code
2. **Updated `app.py`** - Integrated with scheduler
3. **Updated `Procfile`** - Single web service only

## Setup on Leapcell (Much Simpler!)

### Step 1: Push Code to GitHub

```cmd
cd C:\Users\Ethan\OneDrive\Desktop\church-rides
git add .
git commit -m "Integrate watchdog monitoring with APScheduler"
git push origin main
```

### Step 2: Add Environment Variables in Leapcell

Go to your existing service and add these variables:

```
WEBSITE_URL=https://your-actual-app.leapcell.dev
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
ALERT_EMAIL=your-email@gmail.com
CHECK_INTERVAL_MINUTES=5
```

**Important:**
- `CHECK_INTERVAL_MINUTES=5` means check every 5 minutes
- Use your actual Leapcell URL for `WEBSITE_URL`
- Use Gmail App Password (16 characters, no spaces)

### Step 3: Redeploy Your Service

1. In Leapcell dashboard, click **"Deploy"** or **"Redeploy"**
2. Wait for deployment to complete

### Step 4: Verify It's Working

Check your logs - you should see:

```
[2024-01-15 14:30:00] Watchdog monitoring started
Checking https://your-app.leapcell.dev every 5 minutes
Alert email: your-email@gmail.com
[2024-01-15 14:30:01] Running scheduled health check...
[2024-01-15 14:30:02] ✓ Website is healthy
[2024-01-15 14:35:01] Running scheduled health check...
[2024-01-15 14:35:02] ✓ Website is healthy
```

That's it! No worker process, no separate service needed!

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSITE_URL` | - | Your Leapcell app URL (REQUIRED) |
| `SMTP_USERNAME` | - | Your email address (REQUIRED) |
| `SMTP_PASSWORD` | - | Gmail app password (REQUIRED) |
| `ALERT_EMAIL` | - | Where to send alerts (REQUIRED) |
| `CHECK_INTERVAL_MINUTES` | 5 | Minutes between checks |
| `SMTP_SERVER` | smtp.gmail.com | Email server |
| `SMTP_PORT` | 587 | Email port |
| `FAILURE_THRESHOLD` | 2 | Failures before alerting |
| `REQUEST_TIMEOUT` | 10 | Seconds to wait for response |
| `DISABLE_WATCHDOG` | - | Set to 'true' to disable |

### Disable Monitoring (Optional)

To temporarily disable monitoring without removing code:

```
DISABLE_WATCHDOG=true
```

## How It's Different from Standalone Watchdog

### Integrated Version (Current - APScheduler)

**Pros:**
- ✅ Simpler deployment (single service)
- ✅ No separate worker process
- ✅ Automatically starts with your app
- ✅ Uses APScheduler (already in requirements)
- ✅ Perfect for Leapcell

**Cons:**
- ⚠️ If Flask app crashes completely, monitoring stops
- ⚠️ Can't monitor if the entire service is down

### Standalone Version (Previous - watchdog.py)

**Pros:**
- ✅ Completely independent (true external monitoring)
- ✅ Still works if Flask app crashes

**Cons:**
- ❌ Requires separate worker process
- ❌ More complex deployment
- ❌ Leapcell might not support easily

## Which Should You Use?

### Use Integrated (APScheduler) if:
- ✅ You're deploying to Leapcell or similar platforms
- ✅ You want simple, single-service deployment
- ✅ You mainly want to detect crashes/bugs in your code
- ✅ **RECOMMENDED for your use case**

### Use Standalone (watchdog.py) if:
- You have a separate server to run it on
- You need truly independent monitoring
- You want monitoring even if entire platform goes down

## Testing

### Test Locally

```cmd
cd C:\Users\Ethan\OneDrive\Desktop\church-rides

# Set environment variables
set WEBSITE_URL=https://your-app.leapcell.dev
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set ALERT_EMAIL=your-email@gmail.com
set CHECK_INTERVAL_MINUTES=1

# Run Flask app
python app.py
```

You should see watchdog start and check every 1 minute.

### Test Email Configuration

The test script still works:

```cmd
python test_watchdog.py
```

## Advantages for Leapcell

1. **Single service** - No need to add separate worker
2. **Single Procfile** - Just `web: gunicorn app:app`
3. **Automatic start** - Monitoring begins when app starts
4. **Same logs** - Everything in one place
5. **No worker process issues** - Leapcell doesn't need to support workers

## What Happens When You Deploy

1. Leapcell starts your Flask app with Gunicorn
2. Flask app initializes
3. Watchdog scheduler automatically starts
4. Scheduler runs checks every 5 minutes in background
5. Web app continues serving requests normally

Both run simultaneously in the same process!

## Monitoring the Monitor

Check your logs periodically to ensure you see:
- "Running scheduled health check..." every X minutes
- "✓ Website is healthy" messages

If you don't see these, check:
- Environment variables are set correctly
- No error messages in logs
- App deployed successfully

## Troubleshooting

### "Watchdog scheduler not available"

**Cause:** `watchdog_scheduler.py` file missing or import error

**Solution:**
- Verify `watchdog_scheduler.py` is in your repo
- Check for syntax errors in the file
- Redeploy

### "Could not start watchdog monitoring"

**Cause:** Error during scheduler initialization

**Solution:**
- Check logs for specific error message
- Verify environment variables are set
- Check if `apscheduler` is installed

### No health check messages in logs

**Cause:** Scheduler not starting or `DISABLE_WATCHDOG=true`

**Solution:**
- Remove `DISABLE_WATCHDOG` env var if set
- Check for startup errors
- Verify APScheduler is in `requirements.txt`

### Email not sending

**Cause:** Email configuration incorrect

**Solution:**
- Verify Gmail App Password (not regular password)
- Check SMTP_USERNAME and ALERT_EMAIL are set
- Test with `test_watchdog.py` locally first

## Migration from Standalone Watchdog

If you were using the standalone `watchdog.py` approach:

1. ✅ Keep `watchdog.py` (as backup, won't be used)
2. ✅ Use new integrated version
3. ✅ Remove worker from Procfile (already done)
4. ✅ Update environment variables (same ones)
5. ✅ Redeploy

The environment variables are the same, just now they're used by the integrated scheduler instead!

## Summary

**Before (Standalone):**
```
Procfile:
  web: gunicorn app:app
  worker: python watchdog.py  ← Separate process

Deployment: Need to enable worker process
```

**Now (Integrated):**
```
Procfile:
  web: gunicorn app:app  ← Includes monitoring!

Deployment: Just deploy the web service
```

---

**Your monitoring is now built right into your Flask app! 🎉**
