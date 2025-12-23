# Watchdog Quick Start Guide 🚀

Get your watchdog monitoring service running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install requests
```

## Step 2: Configure Email (Gmail Example)

### Get a Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** → **2-Step Verification** (enable if not already)
3. Go back to **Security** → **App passwords**
4. Select **Mail** and **Other (Custom name)**
5. Name it "Church Rides Watchdog"
6. Copy the 16-character password

### Set Environment Variables

**Windows (Command Prompt):**
```cmd
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=xxxx xxxx xxxx xxxx
set ALERT_EMAIL=your-email@gmail.com
set WEBSITE_URL=https://your-app.leapcell.dev
```

**Windows (PowerShell):**
```powershell
$env:SMTP_USERNAME="your-email@gmail.com"
$env:SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
$env:ALERT_EMAIL="your-email@gmail.com"
$env:WEBSITE_URL="https://your-app.leapcell.dev"
```

Replace:
- `your-email@gmail.com` with your actual Gmail address
- `xxxx xxxx xxxx xxxx` with the 16-char app password (remove spaces)
- `https://your-app.leapcell.dev` with your actual website URL

## Step 3: Test Email Configuration

```bash
python test_watchdog.py
```

You should see:
```
✅ SUCCESS! Test email sent successfully!
```

Check your email to confirm it arrived.

## Step 4: Run the Watchdog

```bash
python watchdog.py
```

You should see:
```
[2024-01-15 14:30:00] Church Rides Watchdog Service started
Monitoring: https://your-app.leapcell.dev
Check interval: 300 seconds
[2024-01-15 14:30:05] ✓ Website is healthy
```

## Step 5: Keep It Running

Press `Ctrl+C` to stop. To keep it running permanently:

### Windows - Use Task Scheduler

1. Open **Task Scheduler**
2. Create Basic Task → "Church Rides Watchdog"
3. Trigger: "When I log on"
4. Action: "Start a program"
   - Program: `python.exe` (full path, e.g., `C:\Python311\python.exe`)
   - Arguments: `watchdog.py`
   - Start in: `C:\Users\Ethan\OneDrive\Desktop\church-rides`

### Linux/Mac - Use nohup

```bash
nohup python watchdog.py > watchdog.log 2>&1 &
```

## Customization

Edit the configuration at the top of [watchdog.py](watchdog.py):

- `CHECK_INTERVAL = 300` - Check every 5 minutes (adjust as needed)
- `FAILURE_THRESHOLD = 2` - Alert after 2 consecutive failures

## What Happens When Service Goes Down?

1. Watchdog detects the website is unreachable
2. After 2 consecutive failures (default), it triggers an alert
3. Retrieves all current rides and passengers from the database
4. Sends you an email with:
   - All vehicles and drivers
   - All passengers for each vehicle
   - Contact information
   - Capacity details

5. When service recovers, sends a recovery notification

## Troubleshooting

**"Authentication failed"**
- Make sure you're using the App Password, not your regular password
- Verify 2FA is enabled on Gmail

**"Connection error"**
- Check your WEBSITE_URL is correct
- Verify the website is accessible

**Email not received**
- Check spam/junk folder
- Verify ALERT_EMAIL is correct
- Run `test_watchdog.py` to debug

## Need More Info?

See the full documentation: [WATCHDOG_README.md](WATCHDOG_README.md)

---

That's it! Your watchdog is now monitoring your church rides service 24/7. 🎉
