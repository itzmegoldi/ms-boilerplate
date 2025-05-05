from pydantic import BaseModel


class AppConfig(BaseModel):
    api_version: str
    endpoint: str


class ServerAuthConfig(BaseModel):
    client_name: str
    client_key: str


class ServerConfig(BaseModel):
    host: str
    port: int
    auth: list[ServerAuthConfig]
