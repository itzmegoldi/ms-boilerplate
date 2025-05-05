import os

from src.builder import Clients, set_clients, set_config, set_services
from src.builder.services import Services
from src.config.config import Config
from src.pkg import logging

logger = logging.get_logger()


def fetch_config() -> Config:
    config_path = os.path.join(os.getcwd(), "config/")
    app_env = os.environ.get("APP_ENV", "local")
    logger.info(f"Loading file from {app_env} present at {config_path}")
    return Config.from_yaml(
        config_path,
        app_env,
    )


def build_all_clients(config: Config) -> Clients:
    # TODO: add clients here //NOSONAR
    return Clients().with_pg_db_handler(config=config)


def build_all_services(clients: Clients) -> Services:
    services = Services()
    # TODO: add services here //NOSONAR
    return services


def fetch_config_and_build_services():
    cfg = fetch_config()
    clients = build_all_clients(config=cfg)
    svc = build_all_services(clients)
    set_config(cfg)
    set_clients(clients)
    set_services(svc)
