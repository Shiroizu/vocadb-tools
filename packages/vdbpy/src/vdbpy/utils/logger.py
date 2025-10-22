import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(
    log_filename: str = "", max_bytes: int = 5 * 1024 * 1024, backup_count: int = 3
) -> logging.Logger:
    # 5 * 1024 * 1024 bytes = 5MB ~ 50k lines
    if not log_filename:
        return logging.getLogger(__name__)

    if not log_filename.endswith(".log"):
        log_filename += ".log"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_path = os.path.join(logs_dir, log_filename)

    # Avoid duplicate handlers
    if not logger.handlers:
        # File logger with size-based rotation
        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    return logger
