import argparse
import concurrent.futures
import csv
import dataclasses
import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

from coin_data.config import PUMPFUN_DATA_DIR
from coin_data.exchanges.pumpfun.coin_meta import Token, extract_coin_meta
from coin_data.exchanges.pumpfun.general import fetch_coin_data
from coin_data.exchanges.pumpfun.holders import (
    fetch_24_hour_volume,
    fetch_total_holders,
)
from coin_data.exchanges.pumpfun.market_cap import (
    get_market_cap_with_times,
    get_token_data,
)
from coin_data.exchanges.pumpfun.ohlc import get_ohlc
from coin_data.exchanges.pumpfun.reports import ProcessCsvResponse, process_single_csv
from coin_data.exchanges.pumpfun.token_explorer import (
    PumpfunTokenDataExplorer,
    Transaction,
)
from coin_data.logging import logger
from coin_data.utils.email import send_email

load_dotenv()

# Exponential backoff settings
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # in seconds


def process_token(token: Transaction) -> Token | None:
    """
    Process a single token to fetch data and compute market cap.
    Returns a Token dataclass instance or None if processing fails.
    """
    try:
        logger.info(f"🚀 Processing token {token.token_address}")

        coin_data = fetch_coin_data(token.token_address)
        coin_meta = extract_coin_meta(coin_data)
        if not coin_meta.name:
            logger.error(f"❌ Failed to extract coin meta for: {token.token_address}")
            return None

        volume = fetch_24_hour_volume(coin_meta.raydium_pool)
        holder_count = fetch_total_holders(token.token_address)
        token_response_data = get_token_data(coin_meta.raydium_pool)
        token_data = token_response_data.data
        if not token_data:
            logger.error(f"❌ Failed to fetch token data for: {token.token_address}")
            return None

        relationships = token_data.relationships
        if not relationships:
            logger.error(f"❌ Missing token pair data for: {token.token_address}")
            return None

        included_data = token_response_data.included
        if not included_data:
            logger.error(f"❌ Missing included data for: {token.token_address}")
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
            logger.error(f"❌ Missing circulating supply for: {token.token_address}")
            return None

        token_pair_id = relationships.pairs["data"][0]["id"]
        ohlc_data = get_ohlc(token_data.id, token_pair_id)
        market_cap = get_market_cap_with_times(ohlc_data, circulating_supply)

        token_ = Token(
            name=coin_meta.name,
            symbol=coin_meta.symbol,
            mint=token.token_address,
            volume=volume,
            holder_count=holder_count,
            image_uri=coin_meta.image_uri,
            telegram=coin_meta.telegram,
            twitter=coin_meta.twitter,
            website=coin_meta.website,
            created_timestamp=coin_meta.created_timestamp,
            raydium_pool=coin_meta.raydium_pool,
            highest_market_cap=market_cap.get("highest_market_cap", 0),
            highest_market_cap_timestamp=market_cap.get("highest_market_cap_time", 0),
            lowest_market_cap=market_cap.get("lowest_market_cap", 0),
            lowest_market_cap_timestamp=market_cap.get("lowest_market_cap_time", 0),
            current_market_cap=market_cap.get("current_market_cap", 0),
            current_market_cap_timestamp=market_cap.get("current_market_cap_time", 0),
        )

        logger.info(f"✅ Processed token {coin_meta.name} ({token.token_address})")

        return token_

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

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_token, token) for token in json_data]
            for future in futures:
                future.add_done_callback(write_result_callback)
            concurrent.futures.wait(futures)

    logger.info(f"📝 Results written to {results_file}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve and process Pumpfun token activity."
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Custom date in YYYY-MM-DD format (default: yesterday)",
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send email with the AI report",
    )

    return parser.parse_args()


def get_date_range(explorer: PumpfunTokenDataExplorer, date_arg: str | None):
    if date_arg:
        return explorer.get_day_timestamps(date_arg)
    return explorer.calculate_yesterday_timestamps()


def write_file(file_path: Path, data: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data)


def get_valid_report_path(result: ProcessCsvResponse, results_file: Path) -> str | None:
    if (
        result.status != "success"
        or not result.report_path
        or not os.path.exists(result.report_path)
    ):
        logger.error(f"❌ Failed to generate report for {results_file}")

        if result.message:
            logger.error(result.message)

        return None

    return result.report_path


def load_recipients(csv_path: str) -> list[str]:
    recipients: list[str] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        next(f)  # Skip header
        for line in f:
            recipients.append(line.strip())

    return recipients


def load_email_config() -> dict[str, str] | None:
    required = ["SMTP_SERVER", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"]
    config: dict[str, str] = {}
    missing_keys: list[str] = []

    for key in required:
        value = os.getenv(key)
        if value is None:
            missing_keys.append(key)
        else:
            config[key] = value

    if missing_keys:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_keys)}")
        return None

    return config


def load_report_body(report_path: str) -> str:
    with open(report_path, "r", encoding="utf-8") as f:
        report_json = json.load(f)
    return report_json.get("summary", "")


def main():
    args = parse_arguments()
    explorer = PumpfunTokenDataExplorer()

    start_ts, end_ts = get_date_range(explorer, args.date)
    logger.info(f"🚀 Retrieving token activity from {start_ts} to {end_ts}")

    csv_data = explorer.retrieve_token_activity(start_ts, end_ts)
    output_dir = PUMPFUN_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    date_suffix = (
        args.date
        if args.date
        else time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))
    )
    activities_file = output_dir / f"activities_{date_suffix}.csv"
    results_file = output_dir / f"results_{date_suffix}.csv"

    write_file(activities_file, csv_data)
    json_data = explorer.convert_csv_to_dict(csv_data)
    update_results_csv(json_data, results_file)

    logger.info("🚀 Generating AI reports")
    report_file = (
        os.path.basename(results_file)
        .replace("results_", "report_")
        .replace(".csv", ".json")
    )

    result = process_single_csv(str(results_file), report_file)
    report_path = get_valid_report_path(result, results_file)
    if not report_path:
        return

    logger.info(f"📊 AI report generated: {report_path}")

    email_config = load_email_config()
    if not email_config:
        return

    recipients = load_recipients("emails.csv")
    body = load_report_body(report_path)

    if not args.send_email:
        logger.info("📧 Skipping email send")
        return

    logger.info("📧 Sending email...")

    email_response = send_email(
        smtp_server=email_config["SMTP_SERVER"],
        smtp_port=int(email_config["SMTP_PORT"]),
        username=email_config["SMTP_USERNAME"],
        password=email_config["SMTP_PASSWORD"],
        subject=f"Pumpfun Token Activity Report ({date_suffix})",
        body=body,
        recipients=recipients,
    )

    if email_response.success:
        logger.info("📧 Email sent successfully!")
    else:
        logger.error(f"❌ Failed to send email: {email_response.message}")


if __name__ == "__main__":
    main()
