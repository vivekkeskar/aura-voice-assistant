from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.database.database import init_db
from app.utils.logger import logger
from app.websocket.voice_handler import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AURA Backend Application...")
    await init_db()
    yield
    logger.info("Shutting down AURA Backend Application...")


app = FastAPI(
    title="AURA Voice Assistant API",
    description="Voice-First Personal Productivity Assistant Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"name": "AURA Voice-First Assistant API", "status": "online", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
