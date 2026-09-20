from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_video import (
    router as video_router
)

from app.api.routes_analysis import (
    router as analysis_router
)

from app.api.routes_dataset import (
    router as dataset_router
)


app = FastAPI(

    title=(
        "Vision Based Crowd Congestion "
        "Monitoring and Risk Assessment"
    ),

    version="1.0.0",
)


# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================
# API ROUTERS
# =========================================

app.include_router(
    video_router
)

app.include_router(
    analysis_router
)

app.include_router(
    dataset_router
)


# =========================================
# ROOT
# =========================================

@app.get("/")
def root():

    return {

        "message": (
            "Vision Based Crowd Congestion "
            "Monitoring and Risk Assessment API"
        ),

        "status": "running",

    }


# =========================================
# HEALTH
# =========================================

@app.get("/health")
def health():

    return {

        "status": "ok"

    }