from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="AureaVia API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api import auth  # , rides, drivers, companies, reports, notifications, webhook

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(rides.router, prefix="/api/rides", tags=["rides"])
# app.include_router(drivers.router, prefix="/api/drivers", tags=["drivers"])
# app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
# app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
# app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
# app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
