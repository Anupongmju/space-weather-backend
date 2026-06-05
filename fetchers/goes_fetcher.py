import httpx
from database import get_conn
from psycopg2.extras import execute_values

BASE = "https://services.swpc.noaa.gov/json/goes/primary"

def fetch_xray():
    r = httpx.get(f"{BASE}/xrays-6-hour.json", timeout=30)
    r.raise_for_status()
    data = r.json()

    long_map, short_map = {}, {}
    for d in data:
        t = d['time_tag']
        e = d.get('energy', '')
        flux = float(d.get('flux', 0) or 0)
        sat  = d.get('satellite', 0)
        if '0.1-0.8' in e or '1-8' in e:
            long_map[t]  = (flux, sat)
        elif '0.05-0.4' in e or '0.5-4' in e:
            short_map[t] = (flux, sat)

    records = []
    for t in long_map:
        fl  = long_map[t][0]
        fs  = short_map.get(t, (0, 0))[0]
        sat = long_map[t][1]
        records.append((t, fl, fs, sat))

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO goes_xray (time_tag,flux_long,flux_short,satellite)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               flux_long=EXCLUDED.flux_long,
               flux_short=EXCLUDED.flux_short""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_proton():
    r = httpx.get(f"{BASE}/integral-protons-6-hour.json", timeout=30)
    r.raise_for_status()
    data = r.json()
    records = [(d['time_tag'], d.get('energy',''), float(d.get('flux',0) or 0), d.get('satellite',0)) for d in data]

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO goes_proton (time_tag,energy,flux,satellite)
               VALUES %s
               ON CONFLICT (time_tag,energy) DO UPDATE SET
               flux=EXCLUDED.flux""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_electron():
    r = httpx.get(f"{BASE}/integral-electrons-6-hour.json", timeout=30)
    r.raise_for_status()
    data = r.json()
    records = [(d['time_tag'], d.get('energy',''), float(d.get('flux',0) or 0), d.get('satellite',0)) for d in data]

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO goes_electron (time_tag,energy,flux,satellite)
               VALUES %s
               ON CONFLICT (time_tag,energy) DO UPDATE SET
               flux=EXCLUDED.flux""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_goes_mag():
    r = httpx.get(f"{BASE}/magnetometers-6-hour.json", timeout=30)
    r.raise_for_status()
    data = r.json()
    records = [(
        d['time_tag'],
        float(d.get('Hp',0) or 0), float(d.get('He',0) or 0),
        float(d.get('Hn',0) or 0), float(d.get('Ht',0) or 0),
        d.get('satellite',0)
    ) for d in data]

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO goes_mag (time_tag,hp,he,hn,ht,satellite)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               hp=EXCLUDED.hp, he=EXCLUDED.he,
               hn=EXCLUDED.hn, ht=EXCLUDED.ht""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_goes_wind():
    r = httpx.get("https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json", timeout=30)
    if r.status_code == 404: return 0
    r.raise_for_status()
    data = r.json()
    if not data or len(data) < 2: return 0
    
    records = []
    for row in data[1:]:
        if len(row) < 4: continue
        try:
            time_tag = row[0].replace('.000', 'Z')
            density = float(row[1]) if row[1] is not None else 0.0
            speed = float(row[2]) if row[2] is not None else 0.0
            temp = float(row[3]) if row[3] is not None else 0.0
            records.append((time_tag, density, speed, temp, 0))
        except: continue

    if not records: return 0

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(
            cur,
            """INSERT INTO goes_wind (time_tag,density,speed,temperature,satellite)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               density=EXCLUDED.density, speed=EXCLUDED.speed,
               temperature=EXCLUDED.temperature""",
            records
        )
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_all_goes():
    return {
        "xray":     fetch_xray(),
        "proton":   fetch_proton(),
        "electron": fetch_electron(),
        "mag":      fetch_goes_mag(),
        "wind":     fetch_goes_wind(),
    }