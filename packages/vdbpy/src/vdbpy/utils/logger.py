import inspect
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

_NOISY_LIBRARIES = (
    "asyncio",
    "charset_normalizer",
    "discord",
    "urllib3",
)


def _caller_module_name(default: str = "vdbpy") -> str:
    """Return __name__ of the module that called get_logger()."""
    frame = inspect.currentframe()
    caller = frame.f_back.f_back if frame and frame.f_back else None
    if caller is None:
        return default
    return caller.f_globals.get("__name__", default)


def get_logger(
    log_filename: str = "", max_bytes: int = 5 * 1024 * 1024, backup_count: int = 3
) -> logging.Logger:
    """Return a logger for the calling module."""
    # 5 * 1024 * 1024 bytes = 5MB ~ 50k lines
    if not log_filename:
        return logging.getLogger(_caller_module_name())

    if not log_filename.endswith(".log"):
        log_filename += ".log"

    logs_dir = Path.home() / ".logs" / "vdb"
    if not logs_dir.parent.is_dir():
        logs_dir = Path.cwd()

    log_path = logs_dir / log_filename
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Log path is {log_path}")  # noqa: T201

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)

    # Replace the file handler so the last caller decides the log file
    for handler in [h for h in root.handlers if isinstance(h, RotatingFileHandler)]:
        handler.close()
        root.removeHandler(handler)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    for name in _NOISY_LIBRARIES:
        logging.getLogger(name).setLevel(logging.INFO)

    return root
