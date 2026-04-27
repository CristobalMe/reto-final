import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from config import get_settings
from db import dispose_engine, get_engine, init_engine
import metrics  # noqa: F401 — triggers registration of all metric modules
from routers.closures import router as closures_router
from routers.metrics import router as metrics_router

log = logging.getLogger("main")

_SCHEMA_FILE = pathlib.Path(__file__).parent / "schema.sql"
_SEED_FILE = pathlib.Path(__file__).parent / "seed.sql"
_SEED_CLOSURE_ID = 118888


def _run_sql_file(engine, path: pathlib.Path, label: str) -> None:
    log.warning("running %s …", label)
    sql = path.read_text(encoding="utf-8")
    with engine.connect() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--") and not stmt.startswith("/*!"):
                try:
                    conn.execute(text(stmt))
                except Exception as exc:
                    log.warning("%s statement skipped: %s", label, str(exc)[:120])
        conn.commit()
    log.warning("%s done", label)


def _seed_db(engine) -> None:
    with engine.connect() as conn:
        table_exists = conn.execute(
            text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='inventariomes'")
        ).scalar()

    if not table_exists:
        if _SCHEMA_FILE.exists():
            _run_sql_file(engine, _SCHEMA_FILE, "schema")
        else:
            log.warning("schema.sql not found, cannot initialise DB")
            return

    with engine.connect() as conn:
        already = conn.execute(
            text("SELECT COUNT(*) FROM inventariomes WHERE idinventariomes = :id"),
            {"id": _SEED_CLOSURE_ID},
        ).scalar()

    if already:
        log.info("seed already present, skipping")
        return

    if _SEED_FILE.exists():
        _run_sql_file(engine, _SEED_FILE, "seed")
    else:
        log.warning("seed.sql not found")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_engine(settings)
    _seed_db(get_engine())
    yield
    dispose_engine()


app = FastAPI(title="Talos Fraud Metrics API", version="0.2.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.include_router(metrics_router)
app.include_router(closures_router)


@app.get("/health")
def health():
    return {"status": "ok"}
