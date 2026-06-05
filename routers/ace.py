from fastapi import APIRouter
from database import get_conn
from fetchers.ace_fetcher import fetch_all_ace, fetch_swepam, fetch_mag, fetch_epam, fetch_sis
import psycopg2.extras

router = APIRouter(prefix="/ace", tags=["ACE"])

def query(sql, params=()):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.post("/fetch")
def fetch_all(): return fetch_all_ace()

@router.post("/fetch/swepam")
def fetch_sw(): return {"rows": fetch_swepam()}

@router.post("/fetch/mag")
def fetch_mg(): return {"rows": fetch_mag()}

@router.post("/fetch/epam")
def fetch_ep(): return {"rows": fetch_epam()}

@router.post("/fetch/sis")
def fetch_si(): return {"rows": fetch_sis()}

@router.get("/swepam")
def get_swepam(limit: int = 1440):
    return query("SELECT * FROM ace_swepam ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/mag")
def get_mag(limit: int = 1440):
    return query("SELECT * FROM ace_mag ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/epam")
def get_epam(limit: int = 1440):
    return query("SELECT * FROM ace_epam ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]

@router.get("/sis")
def get_sis(limit: int = 1440):
    return query("SELECT * FROM ace_sis ORDER BY time_tag DESC LIMIT %s", (limit,))[::-1]