import json
import re
from typing import Any


def find_coin_info(raw_data: str) -> dict[str, Any] | None:
    match = re.search(
        r'2:\["\\$","\\$9",null,\{.*?"coin":(\{.*?\})[,}]', raw_data, re.DOTALL
    )
    if match:
        coin_data = match.group(1)
        try:
            parsed_data = json.loads(coin_data)
            result = {
                "name": parsed_data.get("name"),
                "mint": parsed_data.get("mint"),
                "image_uri": parsed_data.get("image_uri"),
                "symbol": parsed_data.get("symbol"),
                "telegram": parsed_data.get("telegram"),
                "twitter": parsed_data.get("twitter"),
                "website": parsed_data.get("website"),
                "created_timestamp": parsed_data.get("created_timestamp"),
            }
            return result
        except json.JSONDecodeError:
            print("Failed to decode coin data")
    else:
        print("Coin data not found")
    return None
