from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from datetime import datetime
from auth_deps import get_current_user, require_admin


from db import get_conn
from loans import router as loans_router
from calendar_routes import router as calendar_router
from items_routes import router as items_router
from auth_routes import router as auth_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="gmach_project API (Python)")

# CORS: allow browser-based frontend (local dev)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(loans_router)
app.include_router(calendar_router)
app.include_router(items_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"ok": True, "service": "gmach api (python)"}