import concurrent.futures
import csv
import json
import threading
import time

from coin_data import logger
from coin_data.exchanges.pumpfun.market_cap import (
    get_market_cap_with_times,
    get_token_data,
)
from coin_data.exchanges.pumpfun.ohlc import get_ohlc
from coin_data.exchanges.pumpfun.parser import find_coin_info
from coin_data.exchanges.pumpfun.request import fetch_coin_data
from coin_data.exchanges.pumpfun.token_explorer import (
    PumpfunTokenDataExplorer,
    Transaction,
)

# Simple retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def process_token(token: Transaction) -> dict[str, str] | None:
    """
    Process a single token to fetch data and compute market cap.
    Returns a dict with the results or None if processing fails.
    """
    try:
        coin_data = fetch_coin_data(token.token_address)
        coin_info = find_coin_info(coin_data)
        logger.info(f"Coin info for {coin_info.name}: {coin_info}")

        # Retry loop for get_token_data and required fields
        token_response_data = None
        token_data = None
        for attempt in range(1, MAX_RETRIES + 1):
            logger.debug(
                f"Token {token.token_address}: Attempt {attempt} for get_token_data"
            )
            token_response_data = get_token_data(coin_info.raydium_pool)
            token_data = token_response_data.data

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
                break  # All required data available

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        else:
            logger.error(
                f"Exceeded maximum retries for token: {token.token_address}. Skipping..."
            )
            return None

        relationship_data = token_data.relationships
        try:
            token_pair_id = relationship_data.pairs["data"][0]["id"]
        except (KeyError, IndexError) as e:
            logger.error(
                f"Failed to retrieve token pair ID for token: {token.token_address}. Error: {e}"
            )
            return None

        # Get OHLC data
        ohlc_data = get_ohlc(token_data.id, token_pair_id)

        # Find circulating supply from the included data
        circulating_supply = None
        for included_data in token_response_data.included:
            if included_data.id == token_data.attributes.base_token_id:
                circulating_supply = included_data.attributes.get("circulating_supply")
                break

        if circulating_supply is None:
            logger.error(
                f"Failed to retrieve circulating supply for token: {token.token_address}"
            )
            return None

        # Calculate market cap data
        mcap = get_market_cap_with_times(ohlc_data, circulating_supply)
        logger.info(f"Market cap data for {coin_info.name}: {mcap}")

        # Return the results as a dictionary.
        return {
            "token_address": token.token_address,
            "coin_name": coin_info.name,
            "market_cap": json.dumps(mcap),
        }
    except Exception as e:
        logger.exception(
            f"Unexpected error processing token {token.token_address}: {e}"
        )
        return None


if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    csv_data = explorer.retrieve_token_activity()
    json_data = explorer.convert_csv_to_dict(csv_data)

    # Create a lock to guard CSV writes
    csv_lock = threading.Lock()

    with open("results.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["token_address", "coin_name", "market_cap"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        csvfile.flush()

        # Define a callback to write each result as soon as it is ready.
        def write_result_callback(
            future: concurrent.futures.Future[dict[str, str] | None]
        ) -> None:
            result = future.result()
            if result is not None:
                with csv_lock:
                    writer.writerow(result)
                    csvfile.flush()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures: list[concurrent.futures.Future[dict[str, str] | None]] = []
            for token in json_data:
                future = executor.submit(process_token, token)
                future.add_done_callback(write_result_callback)
                futures.append(future)

            # Wait for all futures to complete
            concurrent.futures.wait(futures)
