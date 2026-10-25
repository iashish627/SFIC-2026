"""Composable FastAPI entrypoint for the shared CNG Network Intelligence backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.modules.gis.router import router as gis_router
from backend.modules.simulation.router import router as simulator_router
from backend.modules.forecasting.router import router as forecasting_router

app = FastAPI(title="CNG Network Intelligence API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(gis_router)
app.include_router(simulator_router)
app.include_router(forecasting_router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "cng-network-intelligence"}
