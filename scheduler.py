from apscheduler.schedulers.background import BackgroundScheduler
from ingest import DataIngestor
import time

def refresh_data():
    print("Scheduler: Starting data refresh...")
    ingestor = DataIngestor()
    ingestor.ingest()
    print("Scheduler: Data refresh complete.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule to run every 30 days (standard for factsheets)
    # For demo purposes, we can set a shorter interval or just manual trigger
    scheduler.add_job(func=refresh_data, trigger="interval", days=30)
    scheduler.start()
    print("Scheduler started: Data refresh scheduled every 30 days.")
    return scheduler

if __name__ == "__main__":
    # Test run
    refresh_data()
