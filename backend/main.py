"""Composable FastAPI entrypoint for the shared backend.

Run from repository root: uvicorn backend.main:app --reload --port 8000
No station records are fabricated: GIS endpoints return an empty collection until
CNG_STATIONS_CSV points to a source-verified CSV.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.modules.gis.router import router as gis_router

app = FastAPI(title="CNG Network Intelligence API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(gis_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "cng-network-intelligence"}
