import logging
import os


def get_logger(log_filename: str = ""):
    if not log_filename:
        return logging.getLogger(__name__)

    if not log_filename.endswith(".log"):
        log_filename += ".log"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # File logger
    log_path = os.path.join(logs_dir, log_filename)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger
