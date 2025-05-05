from pydantic import BaseModel

from src.config.server import ServerConfig
from src.pkg.config import ConfigMixIn
from src.pkg.db import DatabaseConfig
from src.config.aws import AwsConfig
class Config(BaseModel, ConfigMixIn):
    database: DatabaseConfig
    server: ServerConfig
    aws: AwsConfig
