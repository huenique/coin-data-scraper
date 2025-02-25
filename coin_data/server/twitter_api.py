import json
from typing import List

import httpx
import picologging as logging
from litestar import get

from coin_data.server.constants import HEADERS, TWITTER_SEARCH_API_URL
from coin_data.server.models import (
    AnalysisData,
    ContractData,
    FullResponse,
    TokenInfo,
    UserData,
)
from coin_data.server.utils import convert_keys_to_snake_case

logger = logging.getLogger(__name__)


@get("/twitter/{token_address:str}")
async def get_twitter_data(
    token_address: str, mode: str = "contract"
) -> List[FullResponse]:
    """Fetch Twitter search stream data for a given token address."""
    url = f"{TWITTER_SEARCH_API_URL}?address={token_address}&mode={mode}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)

    if response.status_code != 200:
        return [FullResponse(event="error", data={"message": "Failed to fetch data"})]

    lines = response.text.split("\n")
    parsed_responses: list[FullResponse] = []
    event_type = None

    for line in lines:
        if line.startswith("event:"):
            event_type = line.split(":")[1].strip()
        elif line.startswith("data:"):
            raw_data = line.split(":", 1)[1].strip()
            json_data = json.loads(raw_data)

            if event_type == "tokenInfo":
                parsed_responses.append(
                    FullResponse(
                        event=event_type,
                        data=TokenInfo(
                            **convert_keys_to_snake_case(json_data["tokenInfo"])
                        ),
                    )
                )
            elif event_type == "contractDataComplete":
                parsed_responses.append(
                    FullResponse(
                        event=event_type,
                        data=ContractData(**convert_keys_to_snake_case(json_data)),
                    )
                )
            elif event_type == "userDataComplete":
                parsed_responses.append(
                    FullResponse(
                        event=event_type,
                        data=UserData(**convert_keys_to_snake_case(json_data)),
                    )
                )
            elif event_type == "analysisComplete":
                parsed_responses.append(
                    FullResponse(
                        event=event_type,
                        data=AnalysisData(**convert_keys_to_snake_case(json_data)),
                    )
                )

    return parsed_responses
