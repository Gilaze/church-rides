# Watchdog Setup Guide

## Overview
The watchdog script ([watchdog_scheduler.py](watchdog_scheduler.py)) monitors the health of the church-rides website every 15 minutes using GitHub Actions. If the website is down, it sends an email alert containing all current rides and passenger information.

## How It Works
1. **GitHub Actions** runs the watchdog script every 15 minutes via a scheduled workflow
2. The script checks the `/health` endpoint of your website
3. If the website is down or unreachable:
   - Fetches all rides and passengers from the database
   - Formats a detailed HTML email with all ride information
   - Sends the email to your configured alert address

## Required Environment Variables

You need to configure the following secrets in your GitHub repository settings:

### Navigate to: Repository Settings → Secrets and variables → Actions → New repository secret

### 1. Database Configuration
- **`DATABASE_URL`** (Required)
  - Your PostgreSQL database connection string
  - Example: `postgresql://user:password@host:5432/database`
  - This should already be configured from your existing setup

### 2. Website Monitoring
- **`WEBSITE_URL`** (Required)
  - The URL to monitor for health checks
  - Default: `https://church-rides.up.railway.app/health`
  - Example: `https://your-domain.com/health`

### 3. Email Alert Configuration
- **`ALERT_EMAIL`** (Required)
  - The email address where alerts should be sent
  - Example: `your-email@gmail.com`

- **`SENDER_EMAIL`** (Required)
  - The email address that will send the alerts
  - For Gmail: Your Gmail address
  - Example: `church-rides-bot@gmail.com`

- **`SENDER_PASSWORD`** (Required)
  - The password/app password for the sender email
  - **For Gmail**: You MUST use an App Password (not your regular password)
  - See instructions below for creating a Gmail App Password

- **`SMTP_SERVER`** (Optional)
  - SMTP server address
  - Default: `smtp.gmail.com` (for Gmail)
  - For Outlook/Hotmail: `smtp-mail.outlook.com`
  - For Yahoo: `smtp.mail.yahoo.com`

- **`SMTP_PORT`** (Optional)
  - SMTP server port
  - Default: `587` (TLS)
  - Alternative: `465` (SSL)

## Setting Up Gmail App Password (Recommended)

If you're using Gmail to send alerts, follow these steps:

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** from the left menu
3. Under "Signing in to Google," select **2-Step Verification** (you must have this enabled)
4. At the bottom of the page, select **App passwords**
5. Select **Mail** for the app and **Other** for the device
6. Name it "Church Rides Watchdog"
7. Click **Generate**
8. Copy the 16-character password
9. Use this as your `SENDER_PASSWORD` secret in GitHub

## Setup Instructions

### Step 1: Add GitHub Secrets
1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each of the required secrets listed above

### Step 2: Test the Workflow
1. Go to the **Actions** tab in your repository
2. Select the "Website Health Watchdog" workflow
3. Click **Run workflow** → **Run workflow** (green button)
4. Wait for the workflow to complete
5. Check the logs to ensure it runs successfully

### Step 3: Verify Email Delivery
To test email delivery without waiting for a failure:
1. Temporarily change `WEBSITE_URL` to an invalid URL (e.g., `https://this-will-fail.invalid`)
2. Run the workflow manually
3. Check if you receive the alert email
4. Change `WEBSITE_URL` back to the correct URL

## Workflow Schedule
The watchdog runs every 15 minutes automatically. The schedule is defined in [.github/workflows/watchdog.yml](.github/workflows/watchdog.yml):

```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes
```

## Email Alert Contents
When the website is down, the email will include:
- Alert status and error message
- Total number of rides
- For each ride:
  - Vehicle name
  - Driver name, phone, and email
  - Driver capacity (occupied/total)
  - List of all passengers with their contact info and residence

## Troubleshooting

### Workflow fails with "SENDER_EMAIL or SENDER_PASSWORD not set"
- Make sure you've added both secrets in GitHub repository settings
- Secret names are case-sensitive

### Email not sending (SMTP errors)
- If using Gmail, ensure you're using an App Password, not your regular password
- Check that 2-Step Verification is enabled on your Google account
- Verify `SMTP_SERVER` and `SMTP_PORT` are correct for your email provider
- Some email providers block SMTP access by default - check your email security settings

### Workflow runs but no email received
- Check the GitHub Actions logs for error messages
- Verify the `ALERT_EMAIL` address is correct
- Check your spam/junk folder
- Ensure the sender email has permission to send emails via SMTP

### Database connection errors
- Verify `DATABASE_URL` secret is correctly set
- Ensure the database allows connections from GitHub Actions IP addresses
- Check database credentials are correct

## Files Created
- [watchdog_scheduler.py](watchdog_scheduler.py) - Main watchdog script
- [.github/workflows/watchdog.yml](.github/workflows/watchdog.yml) - GitHub Actions workflow configuration
- [WATCHDOG_SETUP.md](WATCHDOG_SETUP.md) - This documentation file

## Manual Testing
You can test the watchdog script locally:

```bash
# Set environment variables
export DATABASE_URL="your-database-url"
export WEBSITE_URL="https://your-website.com/health"
export ALERT_EMAIL="your-email@gmail.com"
export SENDER_EMAIL="sender@gmail.com"
export SENDER_PASSWORD="your-app-password"

# Run the script
python watchdog_scheduler.py
```

## Stopping the Watchdog
To temporarily disable the watchdog:
1. Go to the **Actions** tab
2. Select "Website Health Watchdog" workflow
3. Click the "..." menu → **Disable workflow**

To re-enable, follow the same steps and click **Enable workflow**.
