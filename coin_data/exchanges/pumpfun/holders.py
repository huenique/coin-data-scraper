import json
from typing import List

from coin_data.exchanges.pumpfun.schema import BubbleGraphData, Holder
from coin_data.requests import APIRequest

CRYPTO_TOOLS = "https://europe-west1-cryptos-tools.cloudfunctions.net"
CRYPTO_TOOLS_BUBBLE_GRAPH = f"{CRYPTO_TOOLS}/get-bubble-graph-data"


def fetch_coin_holders(token: str) -> List[Holder]:
    """
    Fetches coin holders and returns a list of Node objects.
    """
    with APIRequest(CRYPTO_TOOLS) as api_request:
        response = api_request.get(
            endpoint=CRYPTO_TOOLS_BUBBLE_GRAPH,
            params={"token": token, "chain": "sol", "pumpfun": "true"},
        )

        response.raise_for_status()

        if response.body is None:
            raise ValueError(f"{response.body=}")

        body = json.loads(response.body)
        data_model = BubbleGraphData(**body)

        return data_model.nodes
