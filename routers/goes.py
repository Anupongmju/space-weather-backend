from fastapi import APIRouter
from database import get_conn
from fetchers.goes_fetcher import fetch_all_goes
import psycopg2.extras

router = APIRouter(prefix="/goes", tags=["GOES"])

def query(sql, params=()):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/fetch")
def fetch_all(): return fetch_all_goes()

@router.get("/xray")
def get_xray(limit: int = 1440):
    return query("SELECT * FROM goes_xray ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/proton")
def get_proton(limit: int = 1440):
    return query("SELECT * FROM goes_proton ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/electron")
def get_electron(limit: int = 1440):
    return query("SELECT * FROM goes_electron ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/mag")
def get_mag(limit: int = 1440):
    return query("SELECT * FROM goes_mag ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/wind")
def get_wind(limit: int = 1440):
    return query("SELECT * FROM goes_wind ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]