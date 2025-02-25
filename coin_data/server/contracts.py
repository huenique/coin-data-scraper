from typing import Dict, Union

import httpx
from litestar import get

from coin_data.server.constants import CONTRACTS_BATCH_URL, HEADERS
from coin_data.server.models import ForwardedContract
from coin_data.server.utils import convert_keys_to_snake_case


@get("/contracts")
async def get_contracts_batch() -> Union[Dict[str, ForwardedContract], Dict[str, str]]:
    """Fetch contract batch data and return structured JSON."""
    async with httpx.AsyncClient() as client:
        response = await client.get(CONTRACTS_BATCH_URL, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "Failed to fetch contract data"}

    data = response.json()

    return {
        key: ForwardedContract(**convert_keys_to_snake_case(value))
        for key, value in data.items()
    }
