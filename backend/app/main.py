from fastapi import FastAPI, Request
from app.routers import atms, auth, branches, diagnostic_reports, service_calls, users
from app.routers.analytics import router as analytics_router
from fastapi.middleware.cors import CORSMiddleware



app= FastAPI(
    title= "CashCow Branch Operations Command Center",
    description= (
        "Branch operations API for Meridian Trust Bank's autonomous"
        "inspection blah blah blah."
    ),
    version= "0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/version", tags=["health"])
async def version() -> dict[str, str]:
    return {"version": app.version}
