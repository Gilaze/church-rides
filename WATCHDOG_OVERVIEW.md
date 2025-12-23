# Watchdog Service - Complete Overview

## 📁 Files Created

| File | Purpose |
|------|---------|
| `watchdog.py` | Main monitoring script |
| `test_watchdog.py` | Email configuration tester |
| `start_watchdog.bat` | Windows launcher script |
| `start_watchdog.sh` | Linux/Mac launcher script |
| `requirements.watchdog.txt` | Python dependencies |
| `.env.watchdog.example` | Configuration template |
| `WATCHDOG_README.md` | Full documentation |
| `QUICKSTART_WATCHDOG.md` | Quick setup guide |

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    WATCHDOG SERVICE                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │  Every X seconds (default: 300)  │
        │  Check website health            │
        └──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        ┌─────────┐              ┌──────────┐
        │ HEALTHY │              │   DOWN   │
        └─────────┘              └──────────┘
              │                         │
              │                         ▼
              │              ┌─────────────────────┐
              │              │  Increment failure  │
              │              │  counter            │
              │              └─────────────────────┘
              │                         │
              │              ┌─────────────────────┐
              │              │ Reached threshold?  │
              │              │ (default: 2)        │
              │              └─────────────────────┘
              │                         │ YES
              │                         ▼
              │              ┌─────────────────────┐
              │              │ Query database for  │
              │              │ all rides/passengers│
              │              └─────────────────────┘
              │                         │
              │                         ▼
              │              ┌─────────────────────┐
              │              │ Send alert email    │
              │              │ with ride data      │
              │              └─────────────────────┘
              │                         │
              └─────────────────────────┘
                           │
                     (Continue monitoring)
```

## 🎯 Features Breakdown

### 1. Website Monitoring
- **HTTP health checks** every X seconds
- Configurable timeout (default: 10 seconds)
- Supports HTTP and HTTPS
- Checks status codes (200-399 = healthy)

### 2. Smart Alerting
- **Failure threshold**: Only alert after N consecutive failures
- **Cooldown period**: Won't spam emails (1-hour default)
- **Recovery notifications**: Alerts when service comes back online

### 3. Database Integration
- **Reuses existing db.py**: Same database connection as your Flask app
- **Supports both databases**: SQLite (local) and PostgreSQL (production)
- **Read-only access**: Never modifies data

### 4. Email Alerts
- **Detailed ride information**: All vehicles, drivers, and passengers
- **Contact information**: Phone numbers included
- **Capacity tracking**: Shows current capacity vs. max
- **Professional formatting**: Clean, readable email layout

## 📧 Email Alert Example

```
Subject: 🚨 Church Rides Service DOWN - 2024-01-15 14:35:00

ALERT: Church Rides Service is DOWN

The church rides website (https://your-app.leapcell.dev) is
currently not responding.

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

Vehicle: Red Toyota Camry
Driver: Sarah Wilson
Driver Phone: (555) 987-6543
Capacity: 2/3

Passengers:
  1. Mike Brown (Senior) - (555) 111-2222
  2. Lisa Davis (Junior) - (555) 333-4444

------------------------------------------------------------
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSITE_URL` | - | Your website URL to monitor |
| `CHECK_INTERVAL` | 300 | Seconds between checks |
| `SMTP_SERVER` | smtp.gmail.com | Mail server address |
| `SMTP_PORT` | 587 | Mail server port (TLS) |
| `SMTP_USERNAME` | - | Your email address |
| `SMTP_PASSWORD` | - | Your app password |
| `ALERT_EMAIL` | - | Where to send alerts |
| `REQUEST_TIMEOUT` | 10 | HTTP request timeout |
| `FAILURE_THRESHOLD` | 2 | Failures before alerting |
| `DATABASE_URL` | - | PostgreSQL URL (optional) |

### Recommended Settings

**For Production:**
```bash
CHECK_INTERVAL=300       # 5 minutes
FAILURE_THRESHOLD=2      # 2 consecutive failures
REQUEST_TIMEOUT=10       # 10 seconds
```

**For Testing:**
```bash
CHECK_INTERVAL=60        # 1 minute
FAILURE_THRESHOLD=1      # 1 failure
REQUEST_TIMEOUT=5        # 5 seconds
```

**For Low-Priority Monitoring:**
```bash
CHECK_INTERVAL=900       # 15 minutes
FAILURE_THRESHOLD=3      # 3 consecutive failures
REQUEST_TIMEOUT=15       # 15 seconds
```

## 🚀 Deployment Options

### Option 1: Run Locally (Development)
- **Pros**: Easy setup, no cost
- **Cons**: Requires computer to stay on
- **Best for**: Testing, development

### Option 2: Windows Task Scheduler
- **Pros**: Free, runs in background, auto-starts
- **Cons**: Requires Windows PC always on
- **Best for**: Personal use, office computer

### Option 3: Linux Systemd Service
- **Pros**: Robust, auto-restart, logging
- **Cons**: Requires Linux server
- **Best for**: Production on Linux VPS

### Option 4: Cloud Service (Recommended)
- **Pros**: Always running, reliable, independent
- **Cons**: May have costs (many have free tiers)
- **Best for**: Production monitoring

**Free Cloud Options:**
- PythonAnywhere (Free tier)
- Railway (Free tier)
- Render (Free tier)
- Fly.io (Free tier)

## 🔒 Security Best Practices

1. **Never commit credentials**
   - Use environment variables
   - Add `.env.watchdog` to `.gitignore`

2. **Use App Passwords**
   - Don't use your main email password
   - Gmail: Use App Password with 2FA

3. **Limit database access**
   - Watchdog only reads, never writes
   - Use read-only database credentials if possible

4. **Monitor the monitor**
   - Run watchdog on different server than your app
   - Ensures true independence

## 📊 Example Scenarios

### Scenario 1: Website Crashes
```
15:00:00 - ✓ Website healthy
15:05:00 - ✗ Website check failed (1/2)
15:10:00 - ✗ Website check failed (2/2) → ALERT SENT
15:15:00 - ✗ Website still down (no new alert, cooldown)
15:45:00 - ✓ Website healthy → RECOVERY EMAIL SENT
```

### Scenario 2: Brief Hiccup
```
15:00:00 - ✓ Website healthy
15:05:00 - ✗ Website check failed (1/2)
15:10:00 - ✓ Website healthy (failure counter resets)
15:15:00 - ✓ Website healthy
```

### Scenario 3: Network Blip
```
15:00:00 - ✓ Website healthy
15:05:00 - ✗ Timeout (1/2)
15:10:00 - ✗ Timeout (2/2) → ALERT SENT
(Watchdog's internet down for 1 hour)
16:15:00 - ✓ Website healthy → RECOVERY EMAIL SENT
```

## 🛠️ Troubleshooting Guide

| Problem | Solution |
|---------|----------|
| "Authentication failed" | Use App Password, enable 2FA |
| "Connection refused" | Check website URL, verify internet |
| "Database error" | Verify DATABASE_URL, check permissions |
| "Too many emails" | Increase FAILURE_THRESHOLD or CHECK_INTERVAL |
| Script stops running | Use Task Scheduler or systemd |
| No emails received | Check spam folder, verify ALERT_EMAIL |

## 📞 Getting Help

1. **Run the test script first:**
   ```bash
   python test_watchdog.py
   ```

2. **Check the logs** for error messages

3. **Verify configuration:**
   - Are all environment variables set?
   - Is the website URL correct?
   - Is the database accessible?

4. **Test manually:**
   - Can you access the website in a browser?
   - Can you connect to the database?
   - Can you send test emails?

## 📚 Next Steps

1. ✅ Read [QUICKSTART_WATCHDOG.md](QUICKSTART_WATCHDOG.md) for setup
2. ✅ Test with `python test_watchdog.py`
3. ✅ Run manually with `python watchdog.py`
4. ✅ Deploy using Task Scheduler or cloud service
5. ✅ Monitor the logs for any issues

---

**Your church rides service is now protected! 🛡️**
