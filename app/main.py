from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, registrants, attendance

app = FastAPI(title="Conference Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(registrants.router)
app.include_router(attendance.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
