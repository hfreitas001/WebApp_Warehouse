import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, data, movements, orders, admin

app = FastAPI(title="WMS Tractian API", version="0.1.0")
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(movements.router, prefix="/movements", tags=["movements"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/health")
def health():
    return {"status": "ok"}
