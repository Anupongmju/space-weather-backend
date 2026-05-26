import httpx
from datetime import datetime, timedelta, timezone
from database import get_conn

STATIONS = ['OULU','KIEL2','JUNG1','THUL','MOSC']

def fetch_neutron(station='OULU', hours=24):
    end   = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    fmt   = lambda d: d.strftime('%Y-%m-%d%%20%H:%M')

    url = (
        f"https://www.nmdb.eu/nest/draw_graph.php"
        f"?stations[]={station}&tabchoice=revori"
        f"&dtype=corr_for_efficiency&tresolution=60"
        f"&startdate={fmt(start)}&enddate={fmt(end)}&output=ascii"
    )

    r = httpx.get(url, timeout=60)
    r.raise_for_status()

    records = []
    for line in r.text.split('\n'):
        if ';' not in line or line.startswith('#'): continue
        parts = line.strip().split(';')
        if len(parts) < 2: continue
        try:
            time_tag   = parts[0].strip()
            count_rate = float(parts[1].strip())
            records.append((time_tag, station, count_rate))
        except: continue

    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO cosmic_neutron (time_tag,station,count_rate)
           VALUES (%s,%s,%s)
           ON CONFLICT (time_tag,station) DO UPDATE SET
           count_rate=EXCLUDED.count_rate""",
        records
    )
    conn.commit(); conn.close()
    return len(records)

def fetch_all_cosmic():
    return {"neutron_oulu": fetch_neutron('OULU', 24)}