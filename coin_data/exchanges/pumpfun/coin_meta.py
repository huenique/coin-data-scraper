import json
import re

from coin_data.exchanges.pumpfun.schema import Token
from coin_data.logging import logger
from coin_data.utils.encoder import compress_data


def extract_coin_meta(raw_data: str) -> Token:
    match = re.search(
        r'2:\["\$","\$9",null,\{.*?"coin":(\{.*?\})[,}]', raw_data, re.DOTALL
    )

    if match:
        coin_data = match.group(1)

        try:
            parsed_data = json.loads(coin_data)

            return Token(
                name=parsed_data.get("name"),
                symbol=parsed_data.get("symbol"),
                mint=parsed_data.get("mint"),
                volume=0,
                holder_count=0,
                image_uri=parsed_data.get("image_uri"),
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
        not_found = re.search(r"coin doesn't exist or is still indexing", raw_data)
        if not_found:
            logger.error("Coin not found")
        else:
            logger.error(f"Failed to parse coin data: {raw_data}")

    return Token(
        name="",
        symbol="",
        mint="",
        volume=0,
        holder_count=0,
        image_uri="",
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
