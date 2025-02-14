import json
import re
from typing import Any

from coin_data import logger
from coin_data.utils.encoder import compress_data


def find_coin_info(raw_data: str) -> dict[str, Any]:
    match = re.search(
        r'2:\["\$","\$9",null,\{.*?"coin":(\{.*?\})[,}]', raw_data, re.DOTALL
    )

    if match:
        coin_data = match.group(1)

        try:
            parsed_data = json.loads(coin_data)

            return {
                "name": parsed_data.get("name"),
                "mint": parsed_data.get("mint"),
                "image_uri": parsed_data.get("image_uri"),
                "symbol": parsed_data.get("symbol"),
                "telegram": parsed_data.get("telegram"),
                "twitter": parsed_data.get("twitter"),
                "website": parsed_data.get("website"),
                "created_timestamp": parsed_data.get("created_timestamp"),
            }
        except json.JSONDecodeError:
            logger.error(
                f"Failed to parse coin data (compressed): {compress_data(coin_data)}"
            )
    else:
        logger.error(f"Failed to find coin data in response: {compress_data(raw_data)}")

    return {
        "name": None,
        "mint": None,
        "image_uri": None,
        "symbol": None,
        "telegram": None,
        "twitter": None,
        "website": None,
        "created_timestamp": None,
    }
