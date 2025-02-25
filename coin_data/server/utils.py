import re
from typing import Any


def camel_to_snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    name = re.sub(r"([A-Z]+)", r"_\1", name)  # Add underscore before uppercase letters
    return name.lower().lstrip(
        "_"
    )  # Convert to lowercase and remove leading underscores


def convert_keys_to_snake_case(data: dict[str, Any]) -> dict[str, Any]:
    """Convert all keys in a dictionary to snake_case."""
    return {camel_to_snake(k): v for k, v in data.items()}
