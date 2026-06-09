import schedule
import time
from datetime import datetime
from strategies import run_eod_strategy, run_real_time_strategy

def job_eod():
    print(f"[{datetime.now().isoformat()}] Running EOD strategy...")
    try:
        run_eod_strategy()
    except Exception as e:
        print(f"[EOD ERROR] {e}")

def job_rt():
    print(f"[{datetime.now().isoformat()}] Running Real-Time strategy...")
    try:
        run_real_time_strategy()
    except Exception as e:
        print(f"[RT ERROR] {e}")

def run_once_eod():
    job_eod()

def run_once_rt():
    job_rt()

def run_scheduler():
    schedule.every().day.at("09:00").do(job_eod)
    for hour in range(2, 10):
        for minute in [0, 30]:
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job_rt)
    print("Scheduler started. Waiting for scheduled jobs...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "eod":
            run_once_eod()
        elif sys.argv[1] == "rt":
            run_once_rt()
        elif sys.argv[1] == "scheduler":
            run_scheduler()
    else:
        run_scheduler()
