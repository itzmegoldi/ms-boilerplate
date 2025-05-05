from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from ddtrace import patch_all

from src.api.deps import ErrorMiddleware, LoggerInitMiddleware, get_client
from src.builder.helper import fetch_config, fetch_config_and_build_services
from src.pkg import logging


logging.configure_logger(
    default_logger_names=[
        "root",
        "fastapi",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ]
)
logger = logging.get_logger()
patch_all()


@asynccontextmanager
async def lifespan(_: FastAPI):
    fetch_config_and_build_services()
    yield

app = FastAPI()

class HealthCheckModel(BaseModel):
    status: str


@app.get("/health-check/", response_model=HealthCheckModel)
def health_check():
    return {"status": "ok"}

app.add_middleware(middleware_class=ErrorMiddleware)
app.add_middleware(middleware_class=LoggerInitMiddleware)

if __name__=="__main__":
    cfg = fetch_config()
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_config=None)