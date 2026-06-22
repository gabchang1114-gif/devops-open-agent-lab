import sys

from loguru import logger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=settings.app_env == "development",
    )

    logger.info(
        "Logging initialized | service={} environment={} log_level={}",
        settings.service_name,
        settings.app_env,
        settings.log_level.upper(),
    )
