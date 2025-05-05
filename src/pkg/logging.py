import logging
from typing import Any, Optional
from uuid import uuid4

import structlog
from structlog.types import EventDict, Processor


def rename_event_key(_, __, event_dict: EventDict) -> EventDict:  # type: ignore
    """
    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def get_logger(logger_name: str = "app") -> structlog.stdlib.BoundLogger:
    logger = structlog.stdlib.get_logger(logger_name)
    return logger


def _get_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        rename_event_key,
        structlog.processors.format_exc_info,
    ]


def configure_logger(default_logger_names: Optional[list[str]] = None):
    structlog.configure(
        processors=_get_processors()
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    if default_logger_names:
        configure_default_loggers(default_logger_names)


def configure_default_loggers(logger_names: list[str]):
    if not logger_names:
        return

    handler = logging.StreamHandler()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_get_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)
    for logger_name in logger_names:
        if logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
            logging.getLogger(logger_name).handlers.clear()
            logging.getLogger(logger_name).propagate = "access" not in logger_name
            continue

        lgr = (
            logging.getLogger()
            if (logger_name in ("root", ""))
            else logging.getLogger(logger_name)
        )
        lgr.addHandler(handler)
        lgr.setLevel(logging.INFO)


def init_logger_context(request_id: Optional[str] = None):
    structlog.contextvars.clear_contextvars()
    bind_to_context(
        request_id=request_id or uuid4().hex,
    )


def bind_to_context(**kw: Any):
    structlog.contextvars.bind_contextvars(**kw)

def clear_context():
    structlog.contextvars.clear_contextvars()
