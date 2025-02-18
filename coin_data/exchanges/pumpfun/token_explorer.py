import csv
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Tuple

from coin_data import logger
from coin_data.requests import APIRequest

BASE_URL = "api-v2.solscan.io"
ENDPOINT = "v2/account/transfer/export"
PUMPFUN_RAYDIUM_MIGRATION = "39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg"
ACTIVITY_SPL_TRANSFER = "ACTIVITY_SPL_TRANSFER"
RAYDIUM_AUTHORITY_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
WSOL = "So11111111111111111111111111111111111111112"


@dataclass
class Transaction:
    signature: str
    time: str
    action: str
    sender: str
    receiver: str
    amount: str
    flow: str
    value: str
    decimals: str
    token_address: str


class PumpfunTokenDataExplorer:
    def __init__(self, base_url: str = BASE_URL, endpoint: str = ENDPOINT) -> None:
        self.base_url = base_url
        self.endpoint = endpoint

    @staticmethod
    def get_day_timestamps(date_str: str) -> Tuple[int, int]:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        # Start of the given day (00:00:00)
        day_start = int(
            datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                0,
                0,
                0,
                tzinfo=timezone.utc,
            ).timestamp()
        )

        # End of the given day (23:59:59)
        day_end = int(
            datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                23,
                59,
                59,
                999999,
                tzinfo=timezone.utc,
            ).timestamp()
        )

        return day_start, day_end

    @staticmethod
    def calculate_yesterday_timestamps() -> Tuple[int, int]:
        today_midnight = int(time.time()) // 86400 * 86400
        yesterday_start = today_midnight - 86400
        yesterday_end = today_midnight - 1
        return yesterday_start, yesterday_end

    def retrieve_token_activity(self, yesterday_start: int, yesterday_end: int) -> str:
        params = [
            ("address", PUMPFUN_RAYDIUM_MIGRATION),
            ("activity_type[]", ACTIVITY_SPL_TRANSFER),
            ("to", RAYDIUM_AUTHORITY_V4),
            ("exclude_token", WSOL),
            ("block_time[]", str(yesterday_start)),
            ("block_time[]", str(yesterday_end)),
            ("remove_spam", "true"),
        ]

        with APIRequest(self.base_url) as client:
            response = client.get(self.endpoint, params=params)
            response.raise_for_status()

            if response.body is None:
                raise ValueError(f"{response.body=}")

            return response.body

    def convert_csv_to_json(self, csv_data: str) -> str:
        csv_file = StringIO(csv_data)
        reader = csv.DictReader(csv_file)
        transactions = [row for row in reader]
        return json.dumps(transactions, indent=2)

    def convert_csv_to_dict(self, csv_data: str) -> list[Transaction]:
        if not csv_data.strip():
            raise ValueError("CSV data is empty.")

        transactions: list[Transaction] = []
        # List of fields that must be present in each row.
        required_fields = [
            "Signature",
            "Time",
            "Action",
            "From",
            "To",
            "Amount",
            "Flow",
            "Value",
            "Decimals",
            "TokenAddress",
        ]

        try:
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
        except Exception as e:
            raise ValueError("Failed to parse CSV data.") from e

        # Process each row from the CSV.
        for row_num, row in enumerate(
            reader, start=2
        ):  # start=2 to account for the header row.
            # Ensure all required fields exist and are not empty.
            if not all(row.get(field, "").strip() for field in required_fields):
                logger.warning(
                    f"Row {row_num} skipped: missing one or more required fields."
                )
                continue

            try:
                # Convert field values as needed.
                transaction = Transaction(
                    signature=row["Signature"],
                    time=row["Time"],
                    action=row["Action"],
                    sender=row["From"],
                    receiver=row["To"],
                    amount=row["Amount"],
                    flow=row["Flow"],
                    value=row["Value"],
                    decimals=row["Decimals"],
                    token_address=row["TokenAddress"],
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Row {row_num} skipped due to conversion error: {e}")
                continue

            transactions.append(transaction)

        return transactions


if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    yesterday_start, yesterday_end = explorer.calculate_yesterday_timestamps()
    csv_data = explorer.retrieve_token_activity(yesterday_start, yesterday_end)
    json_data = explorer.convert_csv_to_json(csv_data)
    print(json_data)
