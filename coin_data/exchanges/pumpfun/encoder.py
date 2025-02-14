import json
import urllib.parse
from typing import Any


def encode_next_router_state_tree(mint_id: str) -> str:
    """
    Encode the next-router-state-tree parameter for the Pump.fun website.

    Reference:

    ```
    curl 'https://pump.fun/coin/{mintId}?_rsc=1h9q6' \
        -H 'dnt: 1' \
        -H 'next-router-state-tree: %5B%22%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22coin%22%2C%7B%22children%22%3A%5B%5B%22mintId%22%2C%22{mintId}%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fcoin%2F{mintId}%22%2C%22refresh%22%5D%7D%5D%7D%2Cnull%2C%22refetch%22%5D%7D%5D%7D%5D' \
        -H 'rsc: 1'
    ```

    :param mint_id: The mint ID of the token.
    :return: The encoded next-router-state-tree parameter.
    """

    state_tree: list[str | dict[str, Any]] = [
        "",
        {
            "children": [
                "(main)",
                {
                    "children": [
                        "coin",
                        {
                            "children": [
                                ["mintId", mint_id, "d"],
                                {
                                    "children": [
                                        "__PAGE__",
                                        {},
                                        f"/coin/{mint_id}",
                                        "refresh",
                                    ]
                                },
                            ]
                        },
                        None,
                        "refetch",
                    ]
                },
            ]
        },
    ]

    return urllib.parse.quote(json.dumps(state_tree))
