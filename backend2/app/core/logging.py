import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging() -> logging.Logger:
    """
    Configures structured logging for console and rotating file logs.
    """
    log_dir = os.path.join(settings.base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "backend2.log")

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on reload
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024, # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to initialize rotating file logger: {e}\n")

    return logging.getLogger("smartattend")

logger = setup_logging()

