import logging
import time


class CustomFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = f"[{record.levelname}]"
        return super().format(record)


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure handlers are not duplicated
if not logger.handlers:
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        CustomFormatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S UTC"
        )
    )
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler("coind-data-scraper.log")  # Log file name
    file_handler.setFormatter(
        CustomFormatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S UTC"
        )
    )
    logger.addHandler(file_handler)

# Example log message
logger.info("✅ Logging initialized and streaming to both console and file.")
