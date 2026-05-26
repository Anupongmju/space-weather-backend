from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import ace, goes, cosmic,maw
from scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield

app = FastAPI(title="Space Weather API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ace.router)
app.include_router(goes.router)
app.include_router(cosmic.router)
app.include_router(maw.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Space Weather API running"}

@app.post("/fetch/all")
def fetch_all():
    from fetchers.ace_fetcher import fetch_all_ace
    from fetchers.goes_fetcher import fetch_all_goes
    from fetchers.cosmic_fetcher import fetch_all_cosmic
    return {
        "ace":    fetch_all_ace(),
        "goes":   fetch_all_goes(),
        "cosmic": fetch_all_cosmic(),
    }
