# Vehicle Reset Scheduler

## Overview
The vehicle reset system automatically clears passenger bookings and removes non-remembered vehicles every Monday at 12:00 AM PST.

## Files
- `reset_vehicles.py` - Script that performs the weekly reset
- `scheduler.py` - APScheduler-based scheduler that runs the reset automatically
- `migrate_remember_vehicle.py` - One-time migration to add the `remember_vehicle` column

## How It Works

### Reset Logic
Every Monday at 12:00 AM PST:
1. **All passenger bookings are deleted** (clears all passengers from all vehicles)
2. **Vehicles without "Remember Vehicle" enabled are deleted**
3. **Vehicles with "Remember Vehicle" enabled are kept** (but their passengers are still cleared)

### Remember Vehicle Feature
- Drivers can enable "Remember Vehicle" when creating a vehicle
- Drivers can toggle this setting in their profile page
- Vehicles with this feature enabled will persist week-to-week (only passengers are cleared)

## Running the Scheduler

### Local Development
```bash
python scheduler.py
```

This will run continuously and execute the reset every Monday at 12:00 AM PST.

### Production (Leapcell or other hosting)

#### Option 1: Background Process
Run the scheduler as a background process:
```bash
nohup python scheduler.py &
```

#### Option 2: Cron Job
Alternatively, set up a cron job to run the reset script directly:
```bash
# Add to crontab (cron runs in UTC, so 12am PST = 8am UTC)
0 8 * * 1 cd /path/to/church-rides && python reset_vehicles.py
```

#### Option 3: Platform Scheduler
If your hosting platform has a built-in scheduler (like Heroku Scheduler, Railway Cron, etc.), configure it to run:
```bash
python reset_vehicles.py
```
Every Monday at 12:00 AM PST.

## Manual Reset
To manually trigger a reset at any time:
```bash
python reset_vehicles.py
```

## Database Migration
Before using the reset system, run the migration to add the `remember_vehicle` column:
```bash
python migrate_remember_vehicle.py
```

## Dependencies
Added to `requirements.txt`:
- `apscheduler` - For scheduled tasks
- `pytz` - For timezone handling (PST)
