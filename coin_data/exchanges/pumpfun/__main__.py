import concurrent.futures
import csv
import dataclasses
import threading
import time
from pathlib import Path

from coin_data import logger
from coin_data.exchanges.pumpfun.general import fetch_coin_data
from coin_data.exchanges.pumpfun.holders import fetch_coin_holders
from coin_data.exchanges.pumpfun.market_cap import (
    get_market_cap_with_times,
    get_token_data,
)
from coin_data.exchanges.pumpfun.ohlc import get_ohlc
from coin_data.exchanges.pumpfun.parser import Token, find_coin_info
from coin_data.exchanges.pumpfun.token_explorer import (
    PumpfunTokenDataExplorer,
    Transaction,
)

# Simple retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def process_token(token: Transaction) -> Token | None:
    """
    Process a single token to fetch data and compute market cap.
    Returns a Token dataclass instance or None if processing fails.
    """
    try:
        coin_data = fetch_coin_data(token.token_address)
        coin_holders = fetch_coin_holders(token.token_address)
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

        # Calculate market cap data.
        # Here we assume that get_market_cap_with_times returns a dict with the following keys:
        # "highest_market_cap", "highest_market_cap_timestamp", "lowest_market_cap",
        # "lowest_market_cap_timestamp", "current_market_cap", "current_market_cap_timestamp"
        mcap = get_market_cap_with_times(ohlc_data, circulating_supply)
        logger.info(f"Market cap data for {coin_info.name}: {mcap}")

        # Construct and return the Token dataclass instance.
        return Token(
            name=coin_info.name,
            mint=token.token_address,  # Assuming token_address is equivalent to mint
            image_uri=getattr(coin_info, "image_uri", ""),
            symbol=getattr(coin_info, "symbol", ""),
            telegram=getattr(coin_info, "telegram", ""),
            twitter=getattr(coin_info, "twitter", ""),
            website=getattr(coin_info, "website", ""),
            created_timestamp=getattr(coin_info, "created_timestamp", ""),
            raydium_pool=coin_info.raydium_pool,
            virtual_sol_reserves=coin_info.virtual_sol_reserves,
            virtual_token_reserves=coin_info.virtual_token_reserves,
            total_supply=coin_info.total_supply,
            highest_market_cap=mcap.get("highest_market_cap", 0),
            highest_market_cap_timestamp=mcap.get("highest_market_cap_timestamp", 0),
            lowest_market_cap=mcap.get("lowest_market_cap", 0),
            lowest_market_cap_timestamp=mcap.get("lowest_market_cap_timestamp", 0),
            current_market_cap=mcap.get("current_market_cap", 0),
            current_market_cap_timestamp=mcap.get("current_market_cap_timestamp", 0),
            holder_count=coin_holders,
            volume=0,
        )
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

    # Get fieldnames from the Token dataclass
    token_fieldnames = [field.name for field in dataclasses.fields(Token)]

    data_dir = Path("/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / "results.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=token_fieldnames)
        writer.writeheader()
        csvfile.flush()

        # Define a callback to write each result as soon as it is ready.
        def write_result_callback(
            future: concurrent.futures.Future[Token | None],
        ) -> None:
            result = future.result()
            if result is not None:
                with csv_lock:
                    writer.writerow(dataclasses.asdict(result))
                    csvfile.flush()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures: list[concurrent.futures.Future[Token | None]] = []
            for token in json_data:
                future = executor.submit(process_token, token)
                future.add_done_callback(write_result_callback)
                futures.append(future)

            # Wait for all futures to complete
            concurrent.futures.wait(futures)
