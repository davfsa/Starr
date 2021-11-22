import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler


def setup_file_logger() -> None:
    log = logging.getLogger("root")
    log.setLevel(logging.INFO)

    rfh = RotatingFileHandler(
        "./starr/data/logs/main.log",  # FIXME: Move out of there into config file
        maxBytes=512000,
        encoding="utf-8",
        backupCount=10,
    )

    ff = logging.Formatter(
        f"[%(asctime)s] %(levelname)s ||| %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rfh.setFormatter(ff)
    log.addHandler(rfh)

    return log
