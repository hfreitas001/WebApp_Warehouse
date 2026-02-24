import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, data, deposito, inbound_outbound, movements, orders, admin

app = FastAPI(title="WMS Tractian API", version="0.1.0")

# CORS: Vercel + localhost. No Render, defina CORS_ORIGINS se precisar de outros domínios.
_vercel_origin = "https://web-app-warehouse.vercel.app"
_default_origins = [
    _vercel_origin,
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
_cors_raw = (os.getenv("CORS_ORIGINS") or "").strip().strip('"').strip("'")
if _cors_raw:
    _cors_origins = [o.strip().strip('"').strip("'") for o in _cors_raw.split(",") if o.strip()]
else:
    _cors_origins = list(_default_origins)
if _vercel_origin not in _cors_origins:
    _cors_origins.append(_vercel_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(deposito.router, prefix="/data/deposito", tags=["deposito"])
app.include_router(inbound_outbound.router, prefix="/data", tags=["inbound_outbound"])
app.include_router(movements.router, prefix="/movements", tags=["movements"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
def root():
    return {"message": "WMS Tractian API", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok"}
