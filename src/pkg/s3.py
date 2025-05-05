from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import ParseResult, urlparse

import boto3
from mypy_boto3_s3 import S3Client as BotoS3Client
from pydantic import BaseModel

from src.common.types import MimeType


class AwsS3Config(BaseModel):
    endpoint_url: Optional[str] = None


class S3Url:
    url: str
    bucket: str
    key: str
    file_name: str

    def __init__(self, file_url: str):
        parsed_url = self.__parse_s3_url(file_url)
        self.url = file_url
        self.bucket = parsed_url.netloc.split(".")[0]
        self.file_name = parsed_url.path.split("/")[-1]
        self.key = parsed_url.path.lstrip("/")

    def __parse_s3_url(self, url: str) -> ParseResult:
        parsed_url = urlparse(url)
        return parsed_url


@dataclass
class S3Response:
    file_name: str
    mime_type: MimeType
    file_data: bytes


class S3Client:
    def __init__(self, cfg: AwsS3Config):
        self.client: BotoS3Client = boto3.client(  # type: ignore
            "s3",
            endpoint_url=cfg.endpoint_url,
        )

    def download_via_url(
        self, file_url: str, return_as_text: bool = False
    ) -> S3Response:

        s3_url_components = S3Url(file_url=file_url)
        response_obj = self.client.get_object(
            Bucket=s3_url_components.bucket,
            Key=s3_url_components.key,
        )

        content_type = response_obj.get("ContentType")
        file_content = response_obj.get("Body").read()
        file_name = (
            response_obj.get("Metadata").get("original-filename")
            or s3_url_components.file_name
        )
        if return_as_text:
            return S3Response(
                file_name=file_name,
                mime_type=MimeType.TEXT,
                file_data=file_content,
            )

        return S3Response(
            file_name=file_name,
            mime_type=MimeType.parse(content_type, file_name),
            file_data=file_content,
        )

    def upload_file(self, file_path: str, bucket: str, key: str) -> None:
        self.client.upload_file(Filename=file_path, Bucket=bucket, Key=key)

    def _get_file_list_in_bucket(
        self, bucket_name, prefix="", file_name_filter=""
    ) -> List:
        file_names = []
        default_kwargs = {"Bucket": bucket_name, "Prefix": prefix}
        next_token = ""
        while next_token is not None:
            updated_kwargs = default_kwargs.copy()
            if next_token != "":
                updated_kwargs["ContinuationToken"] = next_token
            response = self.client.list_objects_v2(**default_kwargs)
            contents = response.get("Contents")
            for result in contents:  # type: ignore
                key = result.get("Key")
                if file_name_filter in key:  # type: ignore
                    file_names.append(key)
            next_token = response.get("NextContinuationToken")
        return file_names

    def download_all_files_from_bucket(
        self, bucket_name: str, local_path: str, prefix: str, file_name_filter: str
    ):

        local_path = Path(local_path)  # type: ignore
        file_names = self._get_file_list_in_bucket(
            bucket_name=bucket_name, prefix=prefix, file_name_filter=file_name_filter
        )
        for file_name in file_names:
            if file_name_filter not in file_name:
                continue
            file_path = Path.joinpath(local_path, file_name)  # type: ignore
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(bucket_name, file_name, str(file_path))
        return file_names

    def move_s3_file(self, bucket_name, source_key, destination_key) -> None:
        """
        Move an S3 file from one folder to another.

        :param bucket_name: The name of the S3 bucket
        :param source_key: The key (path) of the source file in S3
        :param destination_key: The key (path) of the destination file in S3
        """
        copy_source = {"Bucket": bucket_name, "Key": source_key}
        self.client.copy(copy_source, bucket_name, destination_key)  # type: ignore
        self.client.delete_object(Bucket=bucket_name, Key=source_key)
