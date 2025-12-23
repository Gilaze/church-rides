# Deploying Watchdog as a Separate Service on Leapcell

This guide shows you how to run the watchdog monitoring service as a **separate service** on Leapcell alongside your Flask app.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LEAPCELL PLATFORM                    │
│                                                         │
│  ┌────────────────────┐      ┌─────────────────────┐  │
│  │   Service 1        │      │   Service 2         │  │
│  │   Flask Web App    │      │   Watchdog Monitor  │  │
│  │   (main app)       │      │   (worker)          │  │
│  └────────────────────┘      └─────────────────────┘  │
│            │                           │               │
│            │                           │               │
│            └───────────┬───────────────┘               │
│                        │                               │
│                        ▼                               │
│              ┌──────────────────┐                      │
│              │ PostgreSQL DB    │                      │
│              │ (shared)         │                      │
│              └──────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

## Why This Works Well

✅ **Independent Processes**: Web app and watchdog run separately
✅ **Shared Database**: Both access the same PostgreSQL database
✅ **Easy Management**: All in one Leapcell project
✅ **Cost Effective**: Both services can run on free tier
✅ **True Monitoring**: If web app crashes, watchdog keeps running

## Deployment Methods

### Method 1: Create a Second Leapcell Service (Recommended)

**Step 1: Prepare Your Repository**

Your repository should have these files:
```
church-rides/
├── app.py                    # Your Flask app
├── watchdog.py              # Watchdog script
├── db.py                    # Shared database connection
├── requirements.txt         # All dependencies (includes requests)
├── Procfile                 # For web service: web: gunicorn app:app
└── Procfile.watchdog        # For watchdog service: worker: python watchdog.py
```

**Step 2: Deploy Main Web App (if not already deployed)**

1. Log into Leapcell
2. Create new service from your GitHub repo
3. Leapcell auto-detects `Procfile` and runs the web service
4. Set environment variables for your Flask app

**Step 3: Deploy Watchdog as Second Service**

1. In the same Leapcell project, click **"Add Service"** or **"New Service"**
2. Select the **same GitHub repository**
3. Configure the service:
   - **Name**: `church-rides-watchdog`
   - **Type**: Worker / Background Service
   - **Build Command**: (leave default or blank)
   - **Start Command**: `python watchdog.py`
     - OR if Leapcell uses Procfile: Configure to use `Procfile.watchdog`

**Step 4: Set Environment Variables for Watchdog Service**

In the watchdog service settings, add these environment variables:

```bash
# Database (automatically available in Leapcell, or copy from main service)
DATABASE_URL=<automatically-set-by-leapcell>

# Website to monitor (your main service URL)
WEBSITE_URL=https://your-app.leapcell.dev

# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
ALERT_EMAIL=your-email@gmail.com

# Optional: Customize monitoring
CHECK_INTERVAL=300
FAILURE_THRESHOLD=2
```

**Step 5: Deploy**

Click **"Deploy"** and the watchdog will start running!

### Method 2: Single Service with Multiple Processes

If Leapcell doesn't support multiple services easily, you can use a single service with multiple processes.

**Create a new Procfile:**

Create `Procfile` (replace existing):
```
web: gunicorn app:app
worker: python watchdog.py
```

Leapcell will run both processes in the same container.

⚠️ **Note**: This method means if the container crashes, both web and watchdog go down together. Less ideal but still works.

### Method 3: Use Leapcell's Cron/Scheduled Tasks

If Leapcell supports scheduled tasks (similar to Heroku's scheduler):

1. Create a wrapper script that runs the check once
2. Schedule it to run every 5 minutes
3. Less ideal than continuous monitoring but still functional

## Configuration for Leapcell

### Important Environment Variables

The watchdog needs these variables set in Leapcell:

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `DATABASE_URL` | `postgresql://...` | Yes | Usually auto-set by Leapcell |
| `WEBSITE_URL` | `https://your-app.leapcell.dev` | Yes | Your main service URL |
| `SMTP_USERNAME` | `your-email@gmail.com` | Yes | Your email |
| `SMTP_PASSWORD` | `abcd efgh ijkl mnop` | Yes | Gmail app password |
| `ALERT_EMAIL` | `admin@example.com` | Yes | Where to send alerts |
| `CHECK_INTERVAL` | `300` | No | Seconds between checks |
| `FAILURE_THRESHOLD` | `2` | No | Failures before alert |

### Getting Your Leapcell Website URL

1. Go to your main Flask app service in Leapcell
2. Look for the deployment URL (e.g., `https://church-rides-abc123.leapcell.dev`)
3. Copy this URL
4. Set it as `WEBSITE_URL` in the watchdog service

## Verifying It Works

### Check Watchdog Logs

1. Go to your watchdog service in Leapcell dashboard
2. Click on **"Logs"** or **"View Logs"**
3. You should see output like:

```
[2024-01-15 14:30:00] Church Rides Watchdog Service started
Monitoring: https://your-app.leapcell.dev
Check interval: 300 seconds
------------------------------------------------------------
[2024-01-15 14:30:05] ✓ Website is healthy
[2024-01-15 14:35:05] ✓ Website is healthy
[2024-01-15 14:40:05] ✓ Website is healthy
```

### Test the Alert System

To test if alerts work, you can temporarily:

1. Stop your main Flask web service
2. Wait for 2 check cycles (10 minutes if CHECK_INTERVAL=300)
3. You should receive an alert email
4. Restart your Flask service
5. You should receive a recovery email

## Troubleshooting

### "Can't connect to database"

**Problem**: Watchdog can't access the database

**Solution**: Make sure `DATABASE_URL` is set in the watchdog service environment variables. In Leapcell, this is usually automatically set for all services in the same project.

### "Website always shows as down"

**Problem**: Watchdog thinks the site is down when it's actually up

**Solution**:
- Verify `WEBSITE_URL` is correct (copy from browser)
- Make sure the URL uses `https://` not `http://`
- Check if the web service is actually running

### "No logs appearing"

**Problem**: Watchdog service isn't running

**Solution**:
- Check the start command is correct: `python watchdog.py`
- Verify the service is set to "Worker" or "Background" type
- Check build logs for errors
- Ensure `requirements.txt` includes `requests`

### "Email authentication failed"

**Problem**: Can't send emails

**Solution**:
- Use Gmail App Password, not regular password
- Enable 2FA on Gmail first
- Verify `SMTP_USERNAME` and `SMTP_PASSWORD` are set correctly
- Check for typos in email settings

## Cost Considerations

**Leapcell Free Tier** typically includes:
- Multiple services per project ✅
- Shared database access ✅
- Background workers ✅

**Resource Usage**:
- Watchdog is very lightweight (minimal CPU/memory)
- Only makes HTTP requests every 5 minutes
- Database queries only when service is down
- Should easily fit in free tier limits

## Advantages of Running on Leapcell

✅ **Centralized Management**: Everything in one platform
✅ **Shared Database**: No extra configuration needed
✅ **Easy Deployment**: Push to GitHub, auto-deploy
✅ **Environment Variables**: Easy to manage in UI
✅ **Logs**: View watchdog logs in dashboard
✅ **Cost**: Likely free on free tier

## Limitations

⚠️ **Same Infrastructure**: If entire Leapcell platform has issues, both services go down
⚠️ **Network Issues**: Watchdog and web app share same network, so may not detect some issues

For **maximum reliability**, consider running the watchdog on a completely different platform (Railway, Render, PythonAnywhere). But for most use cases, running on Leapcell as a separate service is totally fine!

## Example Leapcell Project Structure

```
Project: church-rides

├─ Service 1: church-rides-web
│  ├─ Type: Web Service
│  ├─ Start: gunicorn app:app
│  ├─ URL: https://church-rides.leapcell.dev
│  └─ Env Vars: SECRET_KEY, DATABASE_URL (auto)
│
├─ Service 2: church-rides-watchdog
│  ├─ Type: Worker
│  ├─ Start: python watchdog.py
│  ├─ No public URL (background process)
│  └─ Env Vars:
│     - DATABASE_URL (auto)
│     - WEBSITE_URL=https://church-rides.leapcell.dev
│     - SMTP_USERNAME=...
│     - SMTP_PASSWORD=...
│     - ALERT_EMAIL=...
│
└─ Database: PostgreSQL
   └─ Shared by both services
```

## Next Steps

1. ✅ Push your code (including `watchdog.py`) to GitHub
2. ✅ Deploy main Flask app to Leapcell (if not already)
3. ✅ Create second service for watchdog
4. ✅ Set environment variables for watchdog
5. ✅ Deploy and check logs
6. ✅ Test by stopping main service

---

**Your watchdog is now protecting your church rides service from within Leapcell! 🛡️**
