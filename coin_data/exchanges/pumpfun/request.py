from coin_data.exchanges.pumpfun.constants import (
    PUMP_FUN_BASE_URL,
    PUMP_FUN_COIN_ENDPOINT,
)
from coin_data.exchanges.pumpfun.encoder import encode_next_router_state_tree
from coin_data.requests import APIRequest


def fetch_coin_data(mint_id: str) -> str:
    encoded_tree = encode_next_router_state_tree(mint_id)

    with APIRequest(PUMP_FUN_BASE_URL) as api_request:
        response = api_request.get(
            endpoint=f"{PUMP_FUN_COIN_ENDPOINT}/{mint_id}?_rsc=1h9q6",
            headers={
                "accept": "*/*",
                "user-agent": "Mozilla/5.0",
                "dnt": "1",
                "rsc": "1",
                "next-router-state-tree": encoded_tree,
            },
        )

        response.raise_for_status()

        if response.body is None:
            raise ValueError(f"{response.body=}")

        return response.body
