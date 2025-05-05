import json
import uuid
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel

from src.pkg import logging


class AwsSQSConfig(BaseModel):
    region: str
    queue_url: str
    max_number_of_messages: int = 1
    poll_interval_sec: int = 10
    wait_time_sec: int = 20
    endpoint: Optional[str] = None


logger = logging.get_logger()


class SQSMessageSender:
    def __init__(self, config: AwsSQSConfig):
        """
        Initializes the SQSMessageSender with the given configuration.

        :param config: AwsSQSConfig object containing queue configuration.
        """
        self.config = config
        self.sqs_client = boto3.client(
            "sqs",
            region_name=self.config.region,
            endpoint_url=self.config.endpoint,
        )

    def send_message(self, message_body: dict, message_attributes: dict = None) -> dict:
        """
        Sends a message to the SQS queue.

        :param message_body: The body of the message as a dictionary.
        :param message_attributes: Optional attributes for the message.
        :return: The response from the SQS service.
        """
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.config.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes=self._format_message_attributes(message_attributes),
                MessageGroupId="LMS-MESSAGE-GROUP",
                MessageDeduplicationId=str(uuid.uuid4()),
            )
            logger.info(
                "SQS_MESSAGE_TRIGGER_SUCCESS",
                context={
                    "message_body": message_body,
                    "message_attributes": message_attributes,
                },
            )
            return response
        except (BotoCoreError, ClientError) as e:
            logger.info(
                "SQS_MESSAGE_TRIGGER_FAILED",
                context={
                    "message_body": message_body,
                    "message_attributes": message_attributes,
                },
            )
            raise RuntimeError(f"Failed to send message to SQS: {e}")

    @staticmethod
    def _format_message_attributes(attributes: Optional[dict]) -> dict:
        """
        Formats message attributes for SQS.

        :param attributes: A dictionary of attributes.
        :return: A properly formatted dictionary for SQS.
        """
        if not attributes:
            return {}

        formatted_attributes = {
            key: {
                "DataType": "String",
                "StringValue": str(value),
            }
            for key, value in attributes.items()
        }
        return formatted_attributes
