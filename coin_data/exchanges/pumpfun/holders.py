from typing import Any, List

from coin_data.exchanges.pumpfun.schema import BubbleGraphData, Holder
from coin_data.requests import APIRequest

CRYPTO_TOOLS = "europe-west1-cryptos-tools.cloudfunctions.net"
CRYPTO_TOOLS_BUBBLE_GRAPH = "get-bubble-graph-data"


def fetch_coin_holders(token: str) -> List[Holder]:
    """
    Fetches coin holders and returns a list of Node objects.
    """
    with APIRequest(CRYPTO_TOOLS) as api_request:
        response = api_request.get(
            endpoint=CRYPTO_TOOLS_BUBBLE_GRAPH,
            params=[("token", token), ("chain", "sol"), ("pumpfun", "true")],
        )

        response.raise_for_status()

        if response.body is None:
            raise ValueError(f"{response.body=}")

        if not isinstance(response.body, dict):
            raise ValueError(f"{response.body=}")

        data_model = BubbleGraphData(**cast_resp_body(response.body))

        return data_model.nodes


def cast_resp_body(body: dict[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in body.items()}


if __name__ == "__main__":
    holders = fetch_coin_holders("GJAFwWjJ3vnTsrQVabjBVK2TYB1YtRCQXRDfDgUnpump")
    print(holders)
