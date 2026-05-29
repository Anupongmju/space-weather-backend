import httpx
from datetime import datetime, timedelta, timezone
from database import get_conn
from psycopg2.extras import execute_values

STATIONS = ['OULU','KIEL2','JUNG1','THUL','MOSC']

def fetch_neutron(station='OULU', hours=24):
    url = "https://www.nmdb.eu/rt/realtime.txt"
    r = httpx.get(url, timeout=30)
    r.raise_for_status()

    records = []
    for line in r.text.split('\n'):
        if not line or line.startswith('#'): continue
        parts = line.strip().split(';')
        if len(parts) < 3: continue
        
        try:
            time_tag = parts[0].strip()
            st = parts[1].strip()
            if station != 'ALL' and st != station: continue
            
            count_rate = float(parts[2].strip())
            records.append((time_tag, st, count_rate))
        except: continue

    if not records: return 0

    conn = get_conn()
    cur = conn.cursor()
    execute_values(cur, """INSERT INTO cosmic_neutron (time_tag,station,count_rate)
           VALUES %s
           ON CONFLICT (time_tag,station) DO UPDATE SET
           count_rate=EXCLUDED.count_rate""", records)
    conn.commit(); conn.close()
    return len(records)

def fetch_all_cosmic():
    return {"neutron_all": fetch_neutron('ALL')}