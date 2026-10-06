"""
SkillPulse India: Labour-Market Decision Intelligence Platform.
FastAPI Application Entry Point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.db.init_db import init_db
from app.models.labor_market import LaborMarketTimeSeries
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables are created and seed data is populated
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = db.query(LaborMarketTimeSeries).count()
        if count == 0:
            print("[SkillPulse] Seeding initial database and generating synthetic series...")
            init_db()
        else:
            print(f"[SkillPulse] Database already initialized with {count} time series records.")
    finally:
        db.close()
    yield
    # Shutdown logic if any
    pass


app = FastAPI(
    title="SkillPulse India: Decision Intelligence Core",
    description="""
# SkillPulse India API
Decision Intelligence Platform for the Ministry of Skill Development and Entrepreneurship (MSDE).

### Operating Pipeline:
**DETECT → FORECAST → EXPLAIN → SIMULATE → OPTIMIZE**

- **Pilot Coverage:** 3 States (Karnataka, Maharashtra, Odisha), 9 Districts, 5 Sectors, 35 Canonical Skills.
- **Forecasting Horizons:** 3, 6, 12 Months with rolling-window out-of-sample backtesting (WAPE, MAE, MASE).
- **Explainability:** Decoupled TreeSHAP feature attributions and empirical ground indicators.
- **Simulation:** Dynamic cohort lag modeling (Course Duration + Mobilization + Placement delays).
- **Optimization:** Mixed-Integer Constraint Programming via Google OR-Tools CP-SAT.
- **Governance:** Transparent provenance tracking (`is_synthetic: true` demo watermark).
""",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local Next.js client access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount V1 Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "SkillPulse India Decision Intelligence Core",
        "demo_mode": settings.IS_DEMO_MODE,
        "synthetic_data_active": settings.ALLOW_SYNTHETIC_DATA,
        "integer_seats_enforced": settings.ENFORCE_INTEGER_SEATS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
