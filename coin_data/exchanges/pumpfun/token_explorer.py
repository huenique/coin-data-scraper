import csv
import json
import time
from io import StringIO
from typing import Any, Dict, Tuple

from coin_data.requests import APIRequest

BASE_URL = "api-v2.solscan.io"
ENDPOINT = "v2/account/transfer/export"
PUMPFUN_RAYDIUM_MIGRATION = "39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg"
ACTIVITY_SPL_TRANSFER = "ACTIVITY_SPL_TRANSFER"
RAYDIUM_AUTHORITY_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
WSOL = "So11111111111111111111111111111111111111112"


class PumpfunTokenDataExplorer:
    def __init__(self, base_url: str = BASE_URL, endpoint: str = ENDPOINT) -> None:
        self.base_url = base_url
        self.endpoint = endpoint

    def _calculate_yesterday_timestamps(self) -> Tuple[int, int]:
        today_midnight = int(time.time()) // 86400 * 86400
        yesterday_start = today_midnight - 86400
        yesterday_end = today_midnight - 1
        return yesterday_start, yesterday_end

    def retrieve_token_activity(self) -> str:
        yesterday_start, yesterday_end = self._calculate_yesterday_timestamps()

        params: Dict[str, Any] = {
            "address": PUMPFUN_RAYDIUM_MIGRATION,
            "activity_type[]": ACTIVITY_SPL_TRANSFER,
            "to": RAYDIUM_AUTHORITY_V4,
            "exclude_token": WSOL,
            "block_time[]": str(yesterday_start),
            "block_time[]": str(yesterday_end),
            "remove_spam": "true",
        }

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


if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    csv_data = explorer.retrieve_token_activity()
    json_data = explorer.convert_csv_to_json(csv_data)
    print(json_data)
