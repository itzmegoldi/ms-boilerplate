import datetime
from http import HTTPStatus
from typing import Any, List, Optional, Protocol, Tuple

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry

from src.config.common import ExpRetryConfig
from src.pkg import logging


class SalesforcePushError(Exception):
    pass


class SalesforceAuthError(Exception):
    pass


class SfData(BaseModel):
    data: List[dict[Any, Any]]


class SalesforceConfig(BaseModel):
    mock: bool = False
    instance_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    auth_url: str
    timeout_sec: int = 20
    auth_token_expiry_sec: int
    auth_token: Optional[str] = None
    auth_token_expiry: Optional[int] = None
    retry: Optional[ExpRetryConfig]
    sf_sync_endpoint: Optional[str] = None


class ISFClient(Protocol):  # pragma: no cover
    def push_data(
        self,
        sf_endpoint: str,
            data_list: Optional[List[SfData]] = None,
        raw_data: Optional[dict[Any, Any]] = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


logger = logging.get_logger()


class MockSfClient:  # pragma: no cover
    def push_data(
        self,
        sf_endpoint: str,
            data_list: Optional[List[SfData]] = None,
            raw_data: Optional[dict[Any, Any]] = None,
    ) -> dict[str, Any]:
        logger.info("MOCKING_SF_CALL")
        raw_data = []
        for data in data_list:
            raw_data.append(data.model_dump())
        logger.debug(
            "MOCK_SF_DATA",
            data=raw_data,
        )
        return {"failed_rows": [], "success_rows": []}


class SFClient:
    def __init__(self, config: SalesforceConfig) -> None:
        self.config = config
        self.retry: Optional[Retry] = None
        if config.retry:
            self.retry = Retry(
                total=config.retry.max_retries,
                backoff_factor=config.retry.exponent,
            )
        self.common_headers: dict[str, str] = {
            "Content-Type": "application/json",
        }

    def push_data(
        self,
        sf_endpoint: str,
            data_list: Optional[List[SfData]] = None,
            raw_data: Optional[dict[Any, Any]] = None,
    ) -> dict[str, Any]:

        with requests.Session() as session:
            session.mount("https://", HTTPAdapter(max_retries=self.retry))
            url = f"{self.config.instance_url}{sf_endpoint}"
            access_token = self.get_access_token(session)
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            headers.update(self.common_headers)
            if not raw_data:
                raw_data = []
                for data in data_list:
                    raw_data.append(data.model_dump())
            response = session.post(url, json=raw_data, headers=headers)

        if response.status_code != HTTPStatus.OK:
            raise SalesforcePushError(
                {
                    "code": response.status_code,
                    "content": response.content,
                }
            )

        response_data: dict[str, Any] = response.json()

        if response_data.get("errorMessage", None):
            raise SalesforcePushError(response_data)

        return response_data

    def get_access_token(self, session: requests.Session) -> Tuple[str, str]:
        if (
                self.config.auth_token
                and self.config.auth_token_expiry
                > (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
        ):
            return self.config.auth_token

        auth_url = f"{self.config.instance_url}{self.config.auth_url}"
        payload = {
            "grant_type": "password",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "username": self.config.username,
            "password": f"{self.config.password}",
        }

        response = session.post(auth_url, data=payload, timeout=self.config.timeout_sec)

        if response.status_code != HTTPStatus.OK:
            raise SalesforceAuthError

        auth_response = response.json()
        if auth_response.get("access_token", None) is None:
            raise SalesforceAuthError
        auth_token = auth_response.get("access_token")
        self.config.auth_token = auth_token
        self.config.auth_token_expiry = (
                datetime.datetime.now().timestamp() + self.config.auth_token_expiry_sec
        )

        return auth_response.get("access_token")
