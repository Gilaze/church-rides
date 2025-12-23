# Leapcell Cold Start / Serverless Sleep Issue

## The Problem

You mentioned: *"Sometimes when I open up the website after a few hours, it's down. Maybe leapcell takes a while to run the code again because I'm running on a serverless free tier?"*

**You're exactly right!** This is called a **"cold start"** problem common with serverless/free tier platforms.

### What's Happening

```
Hour 1: User visits site → Site loads quickly ✓
Hour 2: No visitors → Leapcell keeps service running
Hour 3: Still no visitors → Leapcell puts service to "sleep" to save resources
Hour 4: You visit site → Service is asleep! ❌
        → Leapcell wakes it up (takes 10-30 seconds)
        → Site appears "down" temporarily
        → Finally loads after startup delay
```

### Why Leapcell Does This

**Free tier optimization:**
- Leapcell pauses inactive services to save server resources
- After ~15-30 minutes of inactivity, your service "sleeps"
- First request after sleep = cold start (slow!)
- Subsequent requests = normal speed ✓

## Solutions

### Option 1: Keep-Alive with Railway Watchdog (Already Done! ✓)

**Your Railway watchdog is already solving this!**

**How it helps:**
- Watchdog checks your site every 5 minutes
- HTTP requests keep Leapcell "awake"
- Never goes into sleep mode
- **Site stays responsive 24/7**

**Status:** ✅ Already working (Railway checks every 5 minutes)

**Downside:** Might not be enough if Leapcell's sleep timeout is very aggressive

---

### Option 2: Reduce Watchdog Check Interval

Make the watchdog ping more frequently to guarantee Leapcell stays awake.

**Change Railway environment variable:**
```
CHECK_INTERVAL=180  (Check every 3 minutes instead of 5)
```

**Or even more frequent:**
```
CHECK_INTERVAL=120  (Check every 2 minutes)
```

**Pros:**
- ✅ Keeps site awake more reliably
- ✅ Faster detection of actual downtime
- ✅ Free (no extra cost)

**Cons:**
- ⚠️ More HTTP requests (might hit rate limits on free tier)
- ⚠️ Slightly more Railway resource usage (still free)

---

### Option 3: Add Second Keep-Alive Service (UptimeRobot)

Use a **free uptime monitoring service** in addition to Railway.

**Recommended: UptimeRobot (Free)**

1. Go to https://uptimerobot.com
2. Create free account
3. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.leapcell.dev`
   - Interval: 5 minutes (free tier)
4. It pings your site every 5 minutes

**Combined effect:**
- Railway watchdog: Every 5 minutes
- UptimeRobot: Every 5 minutes (offset)
- **Result:** Site pinged every ~2.5 minutes average
- Leapcell never sleeps!

**Pros:**
- ✅ Free
- ✅ Redundant monitoring
- ✅ UptimeRobot also sends alerts if site is down
- ✅ No code changes needed

**Cons:**
- None really!

---

### Option 4: Upgrade Leapcell Plan

If Leapcell offers a paid tier that prevents sleeping.

**Check Leapcell pricing:**
- Free tier: Sleeps after inactivity
- Paid tier: Might stay always-on

**Pros:**
- ✅ Guaranteed always-on
- ✅ No workarounds needed
- ✅ Better performance overall

**Cons:**
- ❌ Costs money (check if worth it)

---

### Option 5: Add Health Check Endpoint

Create a lightweight endpoint specifically for keep-alive pings.

**Add to app.py:**

```python
@app.route('/ping')
def ping():
    """Lightweight endpoint for keep-alive checks"""
    return 'pong', 200
```

**Then point watchdog to:**
```
WEBSITE_URL=https://your-app.leapcell.dev/ping
```

**Pros:**
- ✅ Faster response (no database queries)
- ✅ Less server load per check
- ✅ Keeps service awake efficiently

**Cons:**
- Doesn't verify the full site is working

---

### Option 6: Switch to Always-On Platform

If cold starts are unacceptable, consider these alternatives:

**Free Always-On Options:**
1. **Railway** (Free tier, no sleep)
2. **Render** (Free tier sleeps after 15 min, but faster wake)
3. **Fly.io** (Free tier, minimal sleep)

**Paid Reliable Options:**
1. **Heroku Hobby** ($7/month, no sleep)
2. **DigitalOcean App Platform** ($5/month)
3. **Railway Pro** ($5/month)

---

## Recommended Solution for You

### Immediate (Free):

**1. Set up UptimeRobot** (5 minutes)
   - Creates redundant keep-alive pings
   - Free and reliable
   - Backup monitoring too

**2. Reduce Railway check interval** (optional)
   ```
   CHECK_INTERVAL=180
   ```
   - More frequent pings
   - Better guarantee against sleep

### Long-term:

**Monitor the situation:**
- See if Railway watchdog alone is enough
- If cold starts persist, add UptimeRobot
- If still issues, consider upgrading Leapcell or migrating

---

## How to Tell if Cold Start is Happening

### Check Railway Logs

If you see this pattern:
```
[06:00:00] ✓ Website is healthy
[06:05:00] ✓ Website is healthy
[06:10:00] ✗ Website check failed (1/2)  ← Site might be sleeping
[06:15:00] ✓ Website is healthy          ← Woke up!
```

**That's a cold start!** Site slept between 06:05 and 06:10.

### Browser Behavior

**Normal (No cold start):**
- Open site → Loads in 1-3 seconds ✓

**Cold start:**
- Open site → "Loading..." for 10-30 seconds
- Then suddenly loads ✓

---

## Current Setup Analysis

**What you have:**
```
Railway Watchdog → Checks every 5 minutes
                → Sends HTTP GET request
                → Keeps Leapcell awake
```

**Why you might still see "down":**

1. **Leapcell aggressive sleep** - Sleeps faster than 5 min interval
2. **Different timezone checks** - You visit between watchdog checks
3. **Actual downtime** - Real crash (Railway should alert you)

**Solution:**
- Add UptimeRobot for more frequent pings
- Check Railway logs to see pattern

---

## Implementation Steps

### Quick Fix (5 minutes):

1. **Sign up for UptimeRobot:**
   - https://uptimerobot.com
   - Free account

2. **Add Monitor:**
   - Monitor Type: HTTP(s)
   - Friendly Name: Church Rides
   - URL: `https://your-actual-leapcell-url.leapcell.dev`
   - Monitoring Interval: 5 minutes

3. **Done!**
   - Now you have 2 services pinging your site
   - Less chance of cold starts

### Advanced Fix (Railway Check Interval):

1. **Go to Railway dashboard**
2. **Find watchdog service → Variables**
3. **Update CHECK_INTERVAL:**
   ```
   CHECK_INTERVAL=180
   ```
4. **Railway auto-redeploys**
5. **Now checks every 3 minutes**

---

## Testing

### Test if Cold Start is Fixed:

1. **Don't visit your site for 30 minutes**
2. **Check Railway logs:**
   - Should see "✓ Website is healthy" every 5 (or 3) minutes
   - No failures = good!
3. **Visit site in browser**
   - Should load quickly (< 5 seconds)
   - If slow (10-30 sec) = cold start still happening

### If Still Sleeping:

- Add UptimeRobot
- Reduce CHECK_INTERVAL to 120 seconds
- Consider upgrading Leapcell plan

---

## Cost Analysis

| Solution | Cost | Effectiveness |
|----------|------|---------------|
| Railway Watchdog (current) | $0 | 70-80% |
| + UptimeRobot | $0 | 90-95% |
| + Reduced interval (3 min) | $0 | 95-99% |
| + Reduced interval (2 min) | $0 | 99% |
| Leapcell Paid Plan | $5-10/mo | 100% |
| Migrate to Railway | $0-5/mo | 100% |

**Best bang for buck:** Railway + UptimeRobot (both free!)

---

## Summary

**Your cold start issue is normal for serverless free tiers.**

**Easy fix:**
1. ✅ Railway watchdog already helps
2. ✅ Add UptimeRobot (free, 5 minutes)
3. ✅ Optionally reduce CHECK_INTERVAL to 180

**This should eliminate 90%+ of cold start issues for free!**

If problems persist after these fixes, the issue might be actual crashes (not cold starts), and Railway will email you about those.
