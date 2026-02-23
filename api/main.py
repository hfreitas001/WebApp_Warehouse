import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, data, movements, orders, admin

app = FastAPI(title="WMS Tractian API", version="0.1.0")
_default_origins = ",".join(
    f"http://localhost:{p}" for p in (5173, 5174, 5175, 5176, 5177, 5178, 3000)
) + ",http://127.0.0.1:5173,http://127.0.0.1:5174,https://web-app-warehouse.vercel.app"
_cors_raw = os.getenv("CORS_ORIGINS", _default_origins).strip().strip('"').strip("'")
_cors_origins = [o.strip().strip('"').strip("'") for o in _cors_raw.split(",") if o.strip()]
if "https://web-app-warehouse.vercel.app" not in _cors_origins:
    _cors_origins.append("https://web-app-warehouse.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(movements.router, prefix="/movements", tags=["movements"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
def root():
    return {"message": "WMS Tractian API", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok"}
