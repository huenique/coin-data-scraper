import json
import re

from coin_data import logger
from coin_data.exchanges.pumpfun.schema import Holder, Token
from coin_data.utils.encoder import compress_data


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
                virtual_sol_reserves=parsed_data.get("virtual_sol_reserves"),
                virtual_token_reserves=parsed_data.get("virtual_token_reserves"),
                total_supply=parsed_data.get("total_supply"),
                highest_market_cap=0,
                highest_market_cap_timestamp=0,
                lowest_market_cap=0,
                lowest_market_cap_timestamp=0,
                current_market_cap=0,
                current_market_cap_timestamp=0,
                holder_count=[Holder()],
                volume=0,
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
        virtual_sol_reserves=0,
        virtual_token_reserves=0,
        total_supply=0,
        highest_market_cap=0,
        highest_market_cap_timestamp=0,
        lowest_market_cap=0,
        lowest_market_cap_timestamp=0,
        current_market_cap=0,
        current_market_cap_timestamp=0,
        holder_count=[Holder()],
        volume=0,
    )
