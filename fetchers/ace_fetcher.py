import httpx
from database import get_conn
from psycopg2.extras import execute_values

BASE = "https://services.swpc.noaa.gov/text"

def parse_ace_text(text):
    lines = [l for l in text.split('\n') if l.strip() and not l.startswith('#') and not l.startswith(':')]
    return [l.split() for l in lines]

def fetch_swepam():
    try:
        r = httpx.get(f"{BASE}/ace-swepam.txt", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching ACE swepam: {e}")
        return 0
    rows = parse_ace_text(r.text)
    records = []
    for c in rows:
        if len(c) < 10: continue
        try:
            time_tag = f"{c[0]}-{c[1]}-{c[2]} {c[3][:2]}:{c[3][2:]}:00Z"
            density, speed, temp = float(c[7]), float(c[8]), float(c[9])
            status = int(c[6])
            if density < 0 or speed < 0: continue
            records.append((time_tag, density, speed, temp, status))
        except: continue

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO ace_swepam (time_tag,proton_density,bulk_speed,ion_temp,status)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               proton_density=EXCLUDED.proton_density,
               bulk_speed=EXCLUDED.bulk_speed,
               ion_temp=EXCLUDED.ion_temp""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_mag():
    try:
        r = httpx.get(f"{BASE}/ace-magnetometer.txt", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching ACE mag: {e}")
        return 0
    rows = parse_ace_text(r.text)
    records = []
    for c in rows:
        if len(c) < 12: continue
        try:
            time_tag = f"{c[0]}-{c[1]}-{c[2]} {c[3][:2]}:{c[3][2:]}:00Z"
            bx,by,bz,bt = float(c[7]),float(c[8]),float(c[9]),float(c[10])
            lat = float(c[11])
            lon = float(c[12]) if len(c) > 12 else 0.0
            status = int(c[6])
            if bt == -999.9: continue
            records.append((time_tag, bx, by, bz, bt, lat, lon, status))
        except: continue

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO ace_mag (time_tag,bx,by,bz,bt,lat,lon,status)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               bx=EXCLUDED.bx, by=EXCLUDED.by,
               bz=EXCLUDED.bz, bt=EXCLUDED.bt""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_epam():
    try:
        r = httpx.get(f"{BASE}/ace-epam.txt", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching ACE epam: {e}")
        return 0
    rows = parse_ace_text(r.text)
    records = []
    for c in rows:
        if len(c) < 12: continue
        try:
            time_tag = f"{c[0]}-{c[1]}-{c[2]} {c[3][:2]}:{c[3][2:]}:00Z"
            status = int(c[6])
            e38,e175 = float(c[7]),float(c[8])
            p47,p112,p310 = float(c[9]),float(c[10]),float(c[11])
            p761 = float(c[12]) if len(c) > 12 else 0.0
            if e38 < 0: continue
            records.append((time_tag, e38, e175, p47, p112, p310, p761, status))
        except: continue

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO ace_epam (time_tag,e38_53,e175_315,p47_65,p112_187,p310_580,p761_1220,status)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               e38_53=EXCLUDED.e38_53, e175_315=EXCLUDED.e175_315""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_sis():
    try:
        r = httpx.get(f"{BASE}/ace-sis.txt", timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching ACE sis: {e}")
        return 0
    rows = parse_ace_text(r.text)
    records = []
    for c in rows:
        if len(c) < 9: continue
        try:
            time_tag = f"{c[0]}-{c[1]}-{c[2]} {c[3][:2]}:{c[3][2:]}:00Z"
            status = int(c[6])
            p10, p30 = float(c[7]), float(c[8])
            if p10 < 0: continue
            records.append((time_tag, p10, p30, status))
        except: continue

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(cur, """INSERT INTO ace_sis (time_tag,p10,p30,status)
               VALUES %s
               ON CONFLICT (time_tag) DO UPDATE SET
               p10=EXCLUDED.p10, p30=EXCLUDED.p30""", records)
        conn.commit()
    finally:
        conn.close()
    return len(records)

def fetch_all_ace():
    return {
        "swepam": fetch_swepam(),
        "mag":    fetch_mag(),
        "epam":   fetch_epam(),
        "sis":    fetch_sis(),
    }