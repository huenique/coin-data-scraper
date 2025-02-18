import argparse
import concurrent.futures
import csv
import dataclasses
import json
import os
import threading
import time
from pathlib import Path

from coin_data import logger
from coin_data.common import PUMPFUN_DATA_DIR
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

# Exponential backoff settings
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # in seconds


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

        token_response_data = get_token_data(coin_info.raydium_pool)
        token_data = token_response_data.data
        if not token_data:
            logger.error(f"Failed to fetch token data for: {token.token_address}")
            return None

        relationships = token_data.relationships
        if not relationships:
            logger.error(f"Missing token pair data for: {token.token_address}")
            return None

        included_data = token_response_data.included
        if not included_data:
            logger.error(f"Missing included data for: {token.token_address}")
            return None

        circulating_supply = next(
            (
                d.attributes["circulating_supply"]
                for d in included_data
                if d.id == token_data.attributes.base_token_id
            ),
            None,
        )

        if circulating_supply is None:
            logger.error(f"Missing circulating supply for: {token.token_address}")
            return None

        token_pair_id = relationships.pairs["data"][0]["id"]
        ohlc_data = get_ohlc(token_data.id, token_pair_id)
        market_cap = get_market_cap_with_times(ohlc_data, circulating_supply)

        return Token(
            name=coin_info.name,
            mint=token.token_address,
            image_uri=coin_info.image_uri,
            symbol=coin_info.symbol,
            telegram=coin_info.telegram,
            twitter=coin_info.twitter,
            website=coin_info.website,
            created_timestamp=coin_info.created_timestamp,
            raydium_pool=coin_info.raydium_pool,
            virtual_sol_reserves=coin_info.virtual_sol_reserves,
            virtual_token_reserves=coin_info.virtual_token_reserves,
            total_supply=coin_info.total_supply,
            highest_market_cap=market_cap.get("highest_market_cap", 0),
            highest_market_cap_timestamp=market_cap.get(
                "highest_market_cap_timestamp", 0
            ),
            lowest_market_cap=market_cap.get("lowest_market_cap", 0),
            lowest_market_cap_timestamp=market_cap.get(
                "lowest_market_cap_timestamp", 0
            ),
            current_market_cap=market_cap.get("current_market_cap", 0),
            current_market_cap_timestamp=market_cap.get(
                "current_market_cap_timestamp", 0
            ),
            holder_count=len(coin_holders),
            holder_count_meta=json.dumps(coin_holders),
        )
    except Exception as e:
        logger.exception(f"Error processing token {token.token_address}: {e}")
        return None


def update_results_csv(json_data: list[Transaction], results_file: Path):
    """Process tokens and append missing ones to the results CSV."""
    csv_lock = threading.Lock()
    token_fieldnames = [field.name for field in dataclasses.fields(Token)]
    existing_tokens: set[str] = set()

    if os.path.exists(results_file):
        with open(results_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_tokens = {row["mint"] for row in reader}

    json_data = [
        token for token in json_data if token.token_address not in existing_tokens
    ]

    with open(results_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=token_fieldnames)

        if not existing_tokens:
            writer.writeheader()

        def write_result_callback(future: concurrent.futures.Future[Token | None]):
            result = future.result()
            if result:
                with csv_lock:
                    writer.writerow(dataclasses.asdict(result))
                    csvfile.flush()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_token, token) for token in json_data]
            for future in futures:
                future.add_done_callback(write_result_callback)
            concurrent.futures.wait(futures)

    logger.info("Results CSV updated.")


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve and process Pumpfun token activity."
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Custom date in YYYY-MM-DD format (default: yesterday)",
    )

    args = parser.parse_args()

    explorer = PumpfunTokenDataExplorer()

    if args.date:
        yesterday_start, yesterday_end = explorer.get_day_timestamps(args.date)
    else:
        yesterday_start, yesterday_end = explorer.calculate_yesterday_timestamps()

    logger.info(f"Retrieving token activity from {yesterday_start} to {yesterday_end}")

    csv_data = explorer.retrieve_token_activity(yesterday_start, yesterday_end)

    output_dir = PUMPFUN_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    date_suffix = (
        args.date
        if args.date
        else time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))
    )

    activities_file = output_dir / f"activities_{date_suffix}.csv"
    results_file = output_dir / f"results_{date_suffix}.csv"

    # Write activities file
    with open(activities_file, "w") as f:
        f.write(csv_data)

    json_data = explorer.convert_csv_to_dict(csv_data)
    update_results_csv(json_data, results_file)


if __name__ == "__main__":
    main()
