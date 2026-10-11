
from fastapi import FastAPI
from app.api.lots import router as lots_router
from app.api.amhs import router as amhs_router

app = FastAPI(
    title="SmartFab API",
    version="0.1.0"
)
app.include_router(lots_router)
app.include_router(amhs_router)
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SmartFab API"
    }
