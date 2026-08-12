import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, registrants, attendance, events

logger = logging.getLogger("conference_management")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Conference Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(registrants.router)
app.include_router(attendance.router)


@app.get("/health")
async def health():
    # external cron job just to keep the free Render instance 
    # logs that the pings are actually landing (search for "ping").
    logger.info("ping received at %s", datetime.now(timezone.utc).isoformat())
    return {"status": "ok"}