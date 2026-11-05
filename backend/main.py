"""Composable FastAPI entrypoint for the shared CNG Network Intelligence backend."""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from backend.modules.gis.router import router as gis_router
from backend.modules.dashboard.router import router as dashboard_router
from backend.modules.simulation.router import router as simulator_router
from backend.modules.forecasting.router import router as forecasting_router
from backend.modules.scenarios.router import router as scenarios_router
from backend.modules.data_quality.router import router as data_quality_router
from backend.modules.ev_scenarios.router import router as ev_scenarios_router
from backend.modules.planning.router import router as planning_router
from backend.modules.operations.router import router as operations_router

app = FastAPI(title="CNG Network Intelligence API", version="0.4.1")

# Production deployments should set FRONTEND_ORIGIN to the exact public frontend URL.
frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "https://cng-network-intelligence-b82a.onrender.com",
)
allowed_origins = [origin.strip() for origin in frontend_origin.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Reject unexpectedly large request bodies before application processing.
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_000_000:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
    return response


@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "healthy",
        "service": "cng-network-intelligence",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(gis_router)
app.include_router(dashboard_router)
app.include_router(simulator_router)
app.include_router(forecasting_router)
app.include_router(scenarios_router)
app.include_router(data_quality_router)
app.include_router(ev_scenarios_router)
app.include_router(planning_router)
app.include_router(operations_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "cng-network-intelligence", "version": app.version}
