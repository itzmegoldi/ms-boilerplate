from typing import Any

import ddtrace.auto  # type: ignore pylint: disable=unused-import
from ddtrace import patch_all
from pydantic import BaseModel
from sqs_listener import SqsListener  # type: ignore
from typing_extensions import Self

from src.builder import get_config, get_services
from src.builder.helper import fetch_config_and_build_services
from src.pkg import logging, utils
from src.worker import trace_codes

logger = logging.get_logger()
patch_all()


class SqsAttrs(BaseModel):
    attempts: int = 0
    sender_id: str = ""
    sent_time_ms: int = 0
    aws_trace_hdr: str = ""

    @classmethod
    def parse(cls, attrs: Any) -> Self:
        if attrs is None:
            return cls()
        return cls(
            attempts=attrs.get("ApproximateReceiveCount", 0),
            sender_id=attrs.get("SenderId", ""),
            sent_time_ms=attrs.get("SentTimestamp", 0),
            aws_trace_hdr=attrs.get("AWSTraceHeader", ""),
        )


class SimpleConsumer(SqsListener):
    def handle_message(
        self,
        body: Any,
        attributes: Any,  # pylint: disable=unused-argument
        messages_attributes: Any,
    ):
        handler = MessageHandler(self._queue_url)  # type: ignore
        handler.handle_message(body, SqsAttrs.parse(messages_attributes))


class MessageHandler:
    def __init__(self, queue_url: str) -> None:
        self._queue_url = queue_url

    def handle_message(
        self,
        body: Any,
        attributes: SqsAttrs,
    ):
        logging.init_logger_context()
        logging.bind_to_context(app_source="worker")

        logging.bind_to_context(
            attempt=attributes.attempts,
        )

        logger.info(
            trace_codes.WORKER_REQUEST_INITIATED,
            context={
                "sent_time_ms": attributes.sent_time_ms,
                "log_time_ms": utils.time_ms(),
                "queue_url": self._queue_url,
                "sqs": attributes.model_dump(),
            },
        )
        start_time = utils.time_ms()
        try:
            self.__process_message(body)
        except Exception as e:  # pylint: disable=W0718:broad-exception-caught
            logger.exception(
                trace_codes.WORKER_REQUEST_FAILED,
                context={
                    "sent_time_ms": attributes.sent_time_ms,
                    "log_time_ms": utils.time_ms(),
                    "process_time_ms": utils.time_ms() - start_time,
                },
            )
            logging.clear_context()
            raise e

        process_time = utils.time_ms() - start_time

        logger.info(
            trace_codes.WORKER_REQUEST_COMPLETED,
            context={
                "sent_time_ms": attributes.sent_time_ms,
                "log_time_ms": utils.time_ms(),
                "processing_time": process_time,
            },
        )
        logging.clear_context()

    def __process_message(self, body: Any) -> None:
        try:
            #TODO: Implement request validation and get_services here
            pass
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(
                trace_codes.WORKER_INVALID_REQUEST,
            )
            return
        


def main():
    """
    Main function to start the SQS consumer.

    This function reads configuration from the environment, sets up the logger and
    the services, and starts the SQS consumer.

    :return: None
    """
    fetch_config_and_build_services()
    logging.configure_logger(default_logger_names=["root"])
    cfg = get_config()
    consumer = SimpleConsumer(
        queue=cfg.aws.sqs.queue_url.split("/")[-1],
        queue_url=cfg.aws.sqs.queue_url,
        wait_time=cfg.aws.sqs.wait_time_sec,
        interval=cfg.aws.sqs.poll_interval_sec,
        max_number_of_messages=cfg.aws.sqs.max_number_of_messages,
        polling_wait_time_ms=cfg.aws.sqs.wait_time_sec,
        region_name=cfg.aws.sqs.region,
        aws_access_key=cfg.aws.access_key or "",
        aws_secret_key=cfg.aws.aws_secret or "",
        endpoint_name=cfg.aws.sqs.endpoint,
        attribute_names=[
            "ApproximateReceiveCount",
            "SentTimestamp",
            "SenderId",
            "AWSTraceHeader",
        ],
    )
    consumer.listen()


if __name__ == "__main__":
    main()
