import logging
import time


class CustomFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = f"[{record.levelname}]"
        return super().format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        CustomFormatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S UTC"
        )
    )
    logger.addHandler(console_handler)
