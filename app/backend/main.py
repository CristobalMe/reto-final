from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db import dispose_engine, init_engine
import metrics  # noqa: F401 — triggers registration of all metric modules
from routers.closures import router as closures_router
from routers.metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_engine(settings)
    yield
    dispose_engine()


app = FastAPI(title="Talos Fraud Metrics API", version="0.2.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)
app.include_router(closures_router)


@app.get("/health")
def health():
    return {"status": "ok"}
