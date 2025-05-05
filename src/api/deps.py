import time
from typing import Annotated, Awaitable, Callable

from fastapi import Depends, HTTPException, Request, Response, Security, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from uvicorn.protocols.utils import get_path_with_query_string

from src.api import trace_codes
from src.builder import get_config
from src.common.constants import API_KEY_HEADER
from src.pkg import logging

api_key_header = APIKeyHeader(name=API_KEY_HEADER)
logger = logging.get_logger()


def get_client(hdr_key: Annotated[str, Security(api_key_header)]):
    for client in get_config().server.auth:
        if hdr_key == client.client_key:
            return client.client_name

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


GetClientDep = Annotated[str, Depends(get_client)]


class ErrorMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ):

        try:
            response: Response = await call_next(request)
        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

        return response


class LoggerInitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, req_id_header: str = "X-Request-ID"):
        super().__init__(app)
        self.req_id_header = req_id_header

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ):
        req_id = request.headers.get("X-Request-ID", None)

        logging.init_logger_context(request_id=req_id)
        logging.bind_to_context(app_source="web")
        request_url = get_path_with_query_string(request.scope)  # type: ignore
        logger.info(
            trace_codes.REQUEST_INITIATED,
            context={
                "request_url": request_url,
            },
        )
        start_time = time.perf_counter_ns()
        try:
            response: Response = await call_next(request)
        except HTTPException as he:
            logger.exception(
                trace_codes.REQUEST_FAILED,
                context={
                    "process_time": time.perf_counter_ns() - start_time,
                    "request_status": status.HTTP_400_BAD_REQUEST,
                },
            )
            raise he

        process_time = time.perf_counter_ns() - start_time
        logger.info(
            trace_codes.REQUEST_SUCCESS,
            context={
                "process_time": process_time,
                "request_status": response.status_code,
            },
        )
        return response
