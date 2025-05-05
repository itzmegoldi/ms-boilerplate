# db package overriding sql alchemy BaseModel
import os
import ssl
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel as PydBaseModel
from sqlalchemy import BigInteger, Column, String, create_engine
from sqlalchemy import MetaData, Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class DatabaseType(str, Enum):
    POSTGRES = "postgres"


class DbSslConfig(PydBaseModel):
    sslmode: str = "verify-full"
    cert_path: str


class DatabaseConfig(PydBaseModel):
    type: DatabaseType
    username: str
    password: str
    database: str
    url: str
    port: str
    ssl: Optional[DbSslConfig] = None


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    deleted_at = Column(BigInteger, nullable=True, default=None)

    def dict(self):
        return {k: v for k, v in self.__dict__.items() if k != "_sa_instance_state"}


class IHandler(metaclass=ABCMeta):  # pragma: no cover
    @abstractmethod
    def get_session(self) -> Session:
        pass

    @abstractmethod
    async def get_async_session(self) -> AsyncSession:
        pass


class PostgresDbHandler(IHandler):
    config: DatabaseConfig

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.__db_url: str = (
            f"postgresql://{config.username}:{config.password}"
            f"@{config.url}:{config.port}/{config.database}"
        )
        self.__async_db_url: str = (
            f"postgresql+asyncpg://{config.username}:{config.password}"
            f"@{config.url}:{config.port}/{config.database}"
        )
        connect_args: dict[str, str] = {
            "sslmode": "disable",
        }
        if config.ssl is not None:
            connect_args = {
                "sslmode": config.ssl.sslmode,
                "sslrootcert": f"{os.getcwd()}/{config.ssl.cert_path}",
            }

        self.engine = create_engine(
            self.__db_url,
            connect_args=connect_args,
        )
        async_connect_args = {}
        if config.ssl is not None:
            ssl_context = ssl.create_default_context(
                cafile=f"{os.getcwd()}/{config.ssl.cert_path}"
            )
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            async_connect_args = {"ssl": ssl_context}
        self.async_engine = create_async_engine(
            self.__async_db_url, connect_args=async_connect_args
        )
        self.__session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_session(self) -> Session:
        return self.__session_local()

    async def get_async_session(self) -> AsyncSession:
        """Returns an asynchronous session."""
        return async_sessionmaker(
            expire_on_commit=True, bind=self.async_engine, class_=AsyncSession
        )()

    async def load_table(self, table_name) -> Table:
        return Table(
            table_name,
            MetaData(),
            autoload_with=self.engine,
        )
