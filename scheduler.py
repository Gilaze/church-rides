"""
Scheduler for automatic vehicle resets
This script runs continuously and triggers the vehicle reset every Monday at 12:00 AM PST
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from reset_vehicles import reset_vehicles

def main():
    # Create scheduler with PST timezone
    pst = pytz.timezone('America/Los_Angeles')
    scheduler = BlockingScheduler(timezone=pst)

    # Schedule reset_vehicles to run every Monday at 12:00 AM PST
    scheduler.add_job(
        reset_vehicles,
        trigger=CronTrigger(day_of_week='mon', hour=0, minute=0, timezone=pst),
        id='vehicle_reset',
        name='Weekly Vehicle Reset',
        replace_existing=True
    )

    print("Scheduler started. Vehicle reset will run every Monday at 12:00 AM PST")
    print("Press Ctrl+C to exit")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped")

if __name__ == '__main__':
    main()
