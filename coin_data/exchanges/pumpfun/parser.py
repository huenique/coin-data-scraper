import json
import re
from dataclasses import dataclass

from coin_data import logger
from coin_data.utils.encoder import compress_data


@dataclass
class Token:
    name: str
    mint: str
    image_uri: str
    symbol: str
    telegram: str
    twitter: str
    website: str
    created_timestamp: str
    raydium_pool: str
    highest_market_cap: int
    highest_market_cap_timestamp: int
    lowest_market_cap: int
    lowest_market_cap_timestamp: int
    current_market_cap: int
    current_market_cap_timestamp: int


def find_coin_info(raw_data: str) -> Token:
    match = re.search(
        r'2:\["\$","\$9",null,\{.*?"coin":(\{.*?\})[,}]', raw_data, re.DOTALL
    )

    if match:
        coin_data = match.group(1)

        try:
            parsed_data = json.loads(coin_data)

            return Token(
                name=parsed_data.get("name"),
                mint=parsed_data.get("mint"),
                image_uri=parsed_data.get("image_uri"),
                symbol=parsed_data.get("symbol"),
                telegram=parsed_data.get("telegram"),
                twitter=parsed_data.get("twitter"),
                website=parsed_data.get("website"),
                created_timestamp=parsed_data.get("created_timestamp"),
                raydium_pool=parsed_data.get("raydium_pool"),
                highest_market_cap=0,
                highest_market_cap_timestamp=0,
                lowest_market_cap=0,
                lowest_market_cap_timestamp=0,
                current_market_cap=0,
                current_market_cap_timestamp=0,
            )
        except json.JSONDecodeError:
            logger.error(
                f"Failed to parse coin data (compressed): {compress_data(coin_data)}"
            )
    else:
        logger.error(f"Failed to find coin data in response: {compress_data(raw_data)}")

    return Token(
        name="",
        mint="",
        image_uri="",
        symbol="",
        telegram="",
        twitter="",
        website="",
        created_timestamp="",
        raydium_pool="",
        highest_market_cap=0,
        highest_market_cap_timestamp=0,
        lowest_market_cap=0,
        lowest_market_cap_timestamp=0,
        current_market_cap=0,
        current_market_cap_timestamp=0,
    )
