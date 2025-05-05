from typing import Optional

from pydantic import BaseModel

from src.pkg.s3 import AwsS3Config
from src.pkg.sqs import AwsSQSConfig


class AwsConfig(BaseModel):
    sqs: AwsSQSConfig
    s3: AwsS3Config
    access_key: Optional[str] = None
    aws_secret: Optional[str] = None
