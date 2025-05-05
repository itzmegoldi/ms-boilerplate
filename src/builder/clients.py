from typing_extensions import Self

from src.config.config import Config
from src.pkg.db import IHandler, PostgresDbHandler
from src.pkg.s3 import S3Client

class Clients:

    def with_pg_db_handler(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.db_handler: IHandler = PostgresDbHandler(config=config.database)
        return self

    def with_s3_client(self, config: Config) -> Self:
        # pylint: disable=attribute-defined-outside-init
        self.s3_client: S3Client = S3Client(config.aws.s3)
        return self
