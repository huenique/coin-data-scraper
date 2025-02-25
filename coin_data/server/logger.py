import typing

import picologging as logging
from litestar.logging import BaseLoggingConfig
from litestar.types.callable_types import GetLogger


class CustomLoggingConfig(BaseLoggingConfig):
    """Custom logging configuration using picologging with Litestar/Uvicorn formatting."""

    log_exceptions: typing.Literal["always", "debug", "never"] = "always"

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    LOG_LEVEL_WIDTH = 8  # Ensures alignment of log levels

    def configure(self) -> GetLogger:
        """Configures the logging system and returns a callable for retrieving loggers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicate logs
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create console handler with the colored formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.ColoredFormatter())

        # Add the new handler to the root logger
        root_logger.addHandler(console_handler)

        # Return the logger retrieval function, as required by BaseLoggingConfig
        return typing.cast(GetLogger, logging.getLogger)

    class ColoredFormatter(logging.Formatter):
        """Custom formatter for consistent Litestar/Uvicorn log formatting."""

        def format(self, record: logging.LogRecord) -> str:
            log_color = CustomLoggingConfig.COLORS.get(
                record.levelname, CustomLoggingConfig.RESET
            )

            log_color = CustomLoggingConfig.COLORS.get(
                record.levelname, CustomLoggingConfig.RESET
            )

            # Apply color only to the log level (not the colon)
            colored_levelname = (
                f"{log_color}{record.levelname}{CustomLoggingConfig.RESET}:"
            )

            # Match Uvicorn's exact spacing (5 spaces after `:`)
            levelname_padded = f"{colored_levelname}{' ' * 5}"  # 5 spaces after colon

            formatted_message = f"{levelname_padded}{record.getMessage()}"

            return formatted_message
