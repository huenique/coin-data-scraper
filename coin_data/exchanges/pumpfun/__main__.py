import time

from coin_data import logger
from coin_data.exchanges.pumpfun.market_cap import (
    get_market_cap_with_times,
    get_token_data,
)
from coin_data.exchanges.pumpfun.ohlc import get_ohlc
from coin_data.exchanges.pumpfun.parser import find_coin_info
from coin_data.exchanges.pumpfun.request import fetch_coin_data
from coin_data.exchanges.pumpfun.token_explorer import PumpfunTokenDataExplorer

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    csv_data = explorer.retrieve_token_activity()
    json_data = explorer.convert_csv_to_dict(csv_data)

    for token in json_data:
        coin_data = fetch_coin_data(token.token_address)
        coin_info = find_coin_info(coin_data)

        logger.info(f"Coin info for {coin_info.name}: {coin_info}")

        # Retry loop for get_token_data and its related fields
        token_response_data = None
        for attempt in range(1, MAX_RETRIES + 1):
            token_response_data = get_token_data(coin_info.raydium_pool)
            token_data = token_response_data.data

            # Check token_data, relationships, and included data
            if token_data is None:
                logger.error(
                    f"Attempt {attempt}: Failed to retrieve token data for token: {token.token_address}"
                )
            elif token_data.relationships is None:
                logger.error(
                    f"Attempt {attempt}: Failed to retrieve relationship data for token: {token.token_address}"
                )
            elif token_response_data.included is None:
                logger.error(
                    f"Attempt {attempt}: Failed to retrieve included data for token: {token.token_address}"
                )
            else:
                break  # All required data is available

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        else:
            logger.error(
                f"Exceeded maximum retries for token: {token.token_address}. Skipping..."
            )
            continue

        # Extract relationship data and token pair id
        relationship_data = token_data.relationships
        try:
            token_pair_id = relationship_data.pairs["data"][0]["id"]
        except (KeyError, IndexError) as e:
            logger.error(
                f"Failed to retrieve token pair ID for token: {token.token_address}. Error: {e}"
            )
            continue

        # Get OHLC data using token data id and token pair id
        ohlc_data = get_ohlc(token_data.id, token_pair_id)

        # Attempt to find circulating supply in the included data
        circulating_supply = None
        for included_data in token_response_data.included:
            if included_data.id == token_data.attributes.base_token_id:
                circulating_supply = included_data.attributes.get("circulating_supply")
                break

        if circulating_supply is None:
            logger.error(
                f"Failed to retrieve circulating supply for token: {token.token_address}"
            )
            continue

        # Calculate market cap data
        mcap = get_market_cap_with_times(ohlc_data, circulating_supply)
        logger.info(f"Market cap data for {coin_info.name}: {mcap}")
