import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import connect_db, close_db
from .ml.math_solver import load_model
from .api.auth import router as auth_router
from .api.solve import router as solve_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MathLens backend...")
    await connect_db()
    load_model(settings.MODEL_NAME, settings.USE_GPU)
    yield
    await close_db()


app = FastAPI(
    title="MathLens API",
    description="Math Problem Solver from Photo — by Humanoid Maker",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(solve_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "MathLens"}
