import threading
import time
import httpx
import os
from datetime import datetime, timezone, timedelta
from database import get_conn

def cleanup_old_data():
    try:
        conn = get_conn()
        cur = conn.cursor()
        tables = ['ace_swepam','ace_mag','ace_epam','ace_sis',
                  'goes_xray','goes_proton','goes_electron','goes_mag','goes_wind',
                  'cosmic_neutron']
        for table in tables:
            cur.execute(f"""
                DELETE FROM {table}
                WHERE time_tag < NOW() - INTERVAL '90 days'
            """)
        conn.commit()
        conn.close()
        print("[Scheduler] Cleanup old data complete.")
    except Exception as e:
        print(f"[Scheduler] Cleanup Error: {e}")

def ping_self():
    url = os.getenv("RENDER_EXTERNAL_URL", "")
    if not url: return
    try:
        httpx.get(f"{url}/", timeout=10)
        print("[Ping] Self-ping successful")
    except Exception as e:
        print(f"[Ping] Failed: {e}")

def fetch_realtime():
    """ดึงข้อมูล ACE/GOES/Cosmic ทุก 5 นาที"""
    try:
        from fetchers.ace_fetcher import fetch_all_ace
        from fetchers.goes_fetcher import fetch_all_goes
        from fetchers.cosmic_fetcher import fetch_all_cosmic
        fetch_all_ace()
        fetch_all_goes()
        fetch_all_cosmic()
        print(f"[Scheduler] Realtime data updated: {datetime.now(timezone.utc)}")
    except Exception as e:
        print(f"[Scheduler] Realtime Error: {e}")

def start_scheduler():

    # ── Thread 1: ACE/GOES/Cosmic ทุก 5 นาที + ping ────────────────────────
    def realtime_job():
        while True:
            fetch_realtime()
            ping_self()
            time.sleep(5 * 60)  # ทุก 5 นาที

    # ── Thread 2: MAW ทุกวัน 02:00 UTC ────────────────────────────────────
    def maw_job():
        while True:
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            wait_sec = (next_run - now).total_seconds()
            print(f"[Scheduler] Next MAW fetch in {wait_sec/3600:.1f} hrs at {next_run.strftime('%Y-%m-%d %H:%M')} UTC")

            cleanup_old_data()
            time.sleep(wait_sec)

            try:
                from fetchers.maw_fetcher import fetch_maw_today
                result = fetch_maw_today()
                print(f"[Scheduler] MAW auto-fetch: {result}")
            except Exception as e:
                print(f"[Scheduler] MAW Error: {e}")

    # รัน 2 threads พร้อมกัน
    t1 = threading.Thread(target=realtime_job, daemon=True)
    t2 = threading.Thread(target=maw_job,      daemon=True)
    t1.start()
    t2.start()
    print("[Scheduler] Started — Realtime every 5min + MAW daily at 02:00 UTC")