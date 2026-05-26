import threading
import time
from datetime import datetime, timezone
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

def start_scheduler():
    def job():
        while True:
            now = datetime.now(timezone.utc)
            # รอจนถึง 02:00 UTC ของวันถัดไป (ไฟล์ MAW มักอัพเดทหลังเที่ยงคืน UTC)
            from datetime import timedelta
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            wait_sec = (next_run - now).total_seconds()
            print(f"[Scheduler] Next MAW fetch in {wait_sec/3600:.1f} hrs at {next_run.strftime('%Y-%m-%d %H:%M')} UTC")
            
            # Clean up old data before sleeping
            cleanup_old_data()
            
            time.sleep(wait_sec)

            try:
                from fetchers.maw_fetcher import fetch_maw_today
                result = fetch_maw_today()
                print(f"[Scheduler] MAW auto-fetch: {result}")
            except Exception as e:
                print(f"[Scheduler] Error: {e}")

    t = threading.Thread(target=job, daemon=True)
    t.start()
    print("[Scheduler] Started — MAW daily auto-fetch at 02:00 UTC")
