from typing import Any, List

from coin_data.exchanges.pumpfun.schema import (
    BubbleGraphData,
    Holder,
    HolderTotal,
    Volume,
)
from coin_data.exchanges.solscan import (
    SOLSCAN_BASE_URL,
    SOLSCAN_DEFI_POOL_INFO_ENDPOINT,
    SOLSCAN_HOLDER_ENDPOINT,
)
from coin_data.requests import APIRequest

CRYPTO_TOOLS = "europe-west1-cryptos-tools.cloudfunctions.net"
CRYPTO_TOOLS_BUBBLE_GRAPH = "get-bubble-graph-data"


def fetch_24_hour_volume(token: str) -> int:
    with APIRequest(SOLSCAN_BASE_URL) as api_request:
        response = api_request.get(
            endpoint=SOLSCAN_DEFI_POOL_INFO_ENDPOINT,
            params=[("address", token)],
            headers={
                "origin": "https://solscan.io",
                "accept-encoding": "application/json",
            },
        )

        response.raise_for_status()

        if response.body is None or not isinstance(response.body, dict):
            raise ValueError(
                f"Failed to fetch 24-hour volume for token {token}: {response.body or response.error}"
            )

        volume = Volume.from_dict(response.body)

        return volume.data.total_volume_24h


def fetch_total_holders(token: str) -> int:
    with APIRequest(SOLSCAN_BASE_URL) as api_request:
        response = api_request.get(
            endpoint=SOLSCAN_HOLDER_ENDPOINT,
            params=[("address", token)],
            headers={
                "origin": "https://solscan.io",
                "accept-encoding": "application/json",
            },
        )

        response.raise_for_status()

        if response.body is None or not isinstance(response.body, dict):
            raise ValueError(
                f"Failed to fetch total holders for token {token}: {response.body or response.error}"
            )

        holder_total = HolderTotal(**cast_resp_body(response.body))

        return holder_total.data


def fetch_coin_top_holders(token: str) -> List[Holder]:
    """
    Fetches coin holders and returns a list of Node objects.
    """
    with APIRequest(CRYPTO_TOOLS) as api_request:
        response = api_request.get(
            endpoint=CRYPTO_TOOLS_BUBBLE_GRAPH,
            params=[("token", token), ("chain", "sol"), ("pumpfun", "true")],
        )

        response.raise_for_status()

        if response.body is None or not isinstance(response.body, dict):
            raise ValueError(
                f"Failed to fetch top holders for token {token}: {response.body or response.error}"
            )

        data_model = BubbleGraphData(**cast_resp_body(response.body))

        return data_model.nodes


def cast_resp_body(body: dict[str, Any]) -> dict[str, Any]:
    """
    Casts the keys of the response body to strings.
    """
    return {str(k): v for k, v in body.items()}


if __name__ == "__main__":
    # Smoke test
    volume = fetch_24_hour_volume("DtPpwH36Ej2QCKAWwN2266qrHcVKXE17yuezRayFmZ6A")
    print(volume)

    holders = fetch_total_holders("B3qEdjgf6ArJMBoDZcDyuLSoZioZNiYEUXuHKX1kpump")
    print(holders)

    holders = fetch_coin_top_holders("GJAFwWjJ3vnTsrQVabjBVK2TYB1YtRCQXRDfDgUnpump")
    print(holders)
