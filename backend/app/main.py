from fastapi import FastAPI
from app.routers import atms, auth, branches, diagnostic_reports, service_calls, users, roles
from app.routers.analytics import router as analytics_router
from app.routers.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware



app= FastAPI(
    title= "CashCow Branch Operations Command Center",
    description= (
        "Branch operations API for Meridian Trust Bank's autonomous"
        "inspection of branch ATM's."
    ),
    version= "0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://dvgrl2i5sn0a1.cloudfront.net"],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(atms.router)
app.include_router(branches.router)
app.include_router(diagnostic_reports.router)
app.include_router(service_calls.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(analytics_router)
app.include_router(health_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/version", tags=["health"])
async def version() -> dict[str, str]:
    return {"version": app.version}