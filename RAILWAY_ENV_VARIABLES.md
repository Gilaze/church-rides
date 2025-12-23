# Railway Environment Variables - Complete List

This document lists **ALL** environment variables needed for the Railway watchdog service.

## Required Variables

These variables **MUST** be set for the watchdog to function:

### 1. Website Monitoring
```
WEBSITE_URL=https://your-actual-site.leapcell.dev
```
- **Purpose**: The URL of your Leapcell deployment to monitor
- **Example**: `https://church-rides.leapcell.dev`
- **Important**: Replace with your actual Leapcell URL!

### 2. Database Connection
```
DATABASE_URL=postgresql://user:password@host:port/database
```
- **Purpose**: PostgreSQL connection string to access Leapcell database for ride data
- **Where to find**: Leapcell dashboard → Your service → Database → Connection String
- **Format**: `postgresql://username:password@hostname:port/dbname`
- **Example**: `postgresql://user:pass@9qasp5v56q8ckkf5dc.leapcellpool.com:6438/churchrides`
- **Why needed**: Watchdog includes current ride assignments in alert emails

### 3. Email Configuration (Gmail)
```
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
ALERT_EMAIL=your-email@gmail.com
```

**SMTP_USERNAME**:
- Your Gmail address
- Example: `john.doe@gmail.com`

**SMTP_PASSWORD**:
- **NOT your regular Gmail password!**
- Must be a Gmail App Password (16 characters, no spaces)
- How to create:
  1. Go to https://myaccount.google.com/security
  2. Enable 2-Step Verification if not already enabled
  3. Go to https://myaccount.google.com/apppasswords
  4. Create new app password for "Mail"
  5. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
  6. Remove spaces and use in Railway: `xxxxxxxxxxxxxxxx`

**ALERT_EMAIL**:
- Email address to receive alerts
- Can be same as SMTP_USERNAME or different
- Example: `john.doe@gmail.com`

---

## Optional Variables (Have Defaults)

These variables are optional - the watchdog will use sensible defaults if not set:

### Monitoring Behavior
```
CHECK_INTERVAL=300
```
- **Purpose**: How often to check website (in seconds)
- **Default**: 300 (5 minutes)
- **Recommended**: 180-300 (3-5 minutes)
- **Note**: Lower = more frequent checks, keeps Leapcell awake better

```
REQUEST_TIMEOUT=15
```
- **Purpose**: How long to wait for website response (in seconds)
- **Default**: 10 seconds
- **Recommended**: 15 seconds (Leapcell cold starts can be slow)

```
FAILURE_THRESHOLD=2
```
- **Purpose**: How many consecutive failures before sending alert
- **Default**: 2
- **Recommended**: 2 (reduces false alarms)

### Email Ports (Advanced)
```
SMTP_PORT=587
SMTP_SSL_PORT=465
```
- **Purpose**: Email server ports (TLS and SSL)
- **Defaults**: 587 (TLS), 465 (SSL)
- **Note**: Watchdog now tries both automatically!
- **Don't change** unless using different email provider

```
SMTP_SERVER=smtp.gmail.com
```
- **Purpose**: SMTP server hostname
- **Default**: `smtp.gmail.com` (for Gmail)
- **Don't change** unless using different email provider

---

## Complete Railway Configuration

Copy this to Railway dashboard → Your watchdog service → Variables:

```bash
# === REQUIRED - YOU MUST SET THESE ===

# Website to monitor (REPLACE WITH YOUR ACTUAL LEAPCELL URL!)
WEBSITE_URL=https://your-actual-site.leapcell.dev

# Database connection (GET FROM LEAPCELL DASHBOARD!)
DATABASE_URL=postgresql://user:pass@host:port/database

# Email settings (USE YOUR GMAIL AND APP PASSWORD!)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
ALERT_EMAIL=your-email@gmail.com

# === OPTIONAL - CUSTOMIZE IF NEEDED ===

# Check every 3 minutes instead of 5 (keeps Leapcell awake better)
CHECK_INTERVAL=180

# Wait 15 seconds for response (handles Leapcell cold starts)
REQUEST_TIMEOUT=15

# Send alert after 2 consecutive failures
FAILURE_THRESHOLD=2
```

---

## How to Set Variables in Railway

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Select your watchdog project

2. **Navigate to Variables**
   - Click on your watchdog service
   - Click "Variables" tab

3. **Add Variables**
   - Click "New Variable"
   - Enter variable name (e.g., `WEBSITE_URL`)
   - Enter variable value (e.g., `https://your-site.leapcell.dev`)
   - Click "Add"
   - Repeat for all required variables

4. **Deploy**
   - Railway auto-redeploys when variables change
   - Wait ~30 seconds for new deployment
   - Check logs to verify watchdog started successfully

---

## Verification Checklist

After setting variables, verify in Railway logs:

✅ **Startup should show:**
```
Church Rides Watchdog Service started
Monitoring: https://your-site.leapcell.dev
Check interval: 180 seconds
Failure threshold: 2
Alert email: your-email@gmail.com
```

✅ **Health checks should show:**
```
✓ Website is healthy
```

✅ **If website is down, should show:**
```
📧 Trying TLS on smtp.gmail.com:587...
✅ Alert email sent successfully via TLS to your-email@gmail.com
```
OR if TLS fails:
```
⚠️ TLS (port 587) failed: [Errno 101] Network is unreachable
📧 Trying SSL on smtp.gmail.com:465...
✅ Alert email sent successfully via SSL to your-email@gmail.com
```

---

## Troubleshooting

### "Email not configured!" Error
**Problem**: One or more email variables missing

**Solution**: Double-check you set all three:
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `ALERT_EMAIL`

### "SMTP Authentication failed!" Error
**Problem**: Wrong Gmail App Password

**Solution**:
1. Create NEW App Password at https://myaccount.google.com/apppasswords
2. Copy 16-character password (remove spaces!)
3. Update `SMTP_PASSWORD` in Railway
4. Example: `abcd efgh ijkl mnop` → `abcdefghijklmnop`

### "Network is unreachable" for BOTH ports
**Problem**: Railway blocking all outbound SMTP

**Solution**:
Railway free tier may block SMTP entirely. Alternatives:
1. **Upgrade Railway plan** (Hobby plan allows SMTP)
2. **Use email API instead** (SendGrid, Mailgun, Resend)
3. **Deploy watchdog elsewhere** (Render, Fly.io, Heroku)

### "connection to server... failed: server closed the connection"
**Problem**: Wrong DATABASE_URL or Leapcell database unreachable

**Solution**:
1. Get fresh connection string from Leapcell dashboard
2. Verify format: `postgresql://user:pass@host:port/dbname`
3. Update `DATABASE_URL` in Railway

---

## Summary

**Minimum required variables:**
1. `WEBSITE_URL` - Your Leapcell site URL
2. `DATABASE_URL` - Leapcell PostgreSQL connection string
3. `SMTP_USERNAME` - Your Gmail address
4. `SMTP_PASSWORD` - Gmail App Password (16 chars)
5. `ALERT_EMAIL` - Where to send alerts

**Recommended optional variables:**
- `CHECK_INTERVAL=180` (check every 3 minutes)
- `REQUEST_TIMEOUT=15` (handle cold starts)

Set these in Railway dashboard → Variables, and the watchdog will automatically restart with the new configuration!
