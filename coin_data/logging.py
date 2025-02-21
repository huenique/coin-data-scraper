import logging
import sys
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
    # Console Handler (set encoding explicitly)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        CustomFormatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S UTC"
        )
    )

    # Force UTF-8 encoding for Windows
    if sys.platform.startswith("win"):
        import io

        console_handler.stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    logger.addHandler(console_handler)

    # File Handler (use UTF-8 encoding)
    file_handler = logging.FileHandler("coin-data-scraper.log", encoding="utf-8")
    file_handler.setFormatter(
        CustomFormatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S UTC"
        )
    )
    logger.addHandler(file_handler)

# Example log message
logger.info("✅ Logging initialized and streaming to both console and file.")
