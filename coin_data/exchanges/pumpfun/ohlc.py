import datetime
import time
from dataclasses import dataclass
from typing import Any

from coin_data import logger
from coin_data.exchanges.common import DefaultMixin
from coin_data.exchanges.pumpfun.constants import (
    GECKO_TERMINAL_BASE_URL,
    GECKO_TERMINAL_CANDLESTICKS_ENDPOINT,
    PUMPFUN_LAUNCH_DATE,
    PUMPFUN_LAUNCH_DATE_TIMESTAMP,
)
from coin_data.requests import APIRequest


@dataclass
class Candle(DefaultMixin):
    dt: str
    o: float
    h: float
    l: float
    c: float
    v: float


@dataclass
class CandleData(DefaultMixin):
    meta: dict[str, Any]
    data: list[Candle]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CandleData":
        candles = [Candle(**item) for item in d.get("data", [])]
        return cls(meta=d.get("meta", {}), data=candles)


def get_ohlc(pool_id: str, pair_id: str) -> CandleData:
    """
    https://app.geckoterminal.com/api/p1/candlesticks/{pool_id}/{pair_id}?resolution=60&from_timestamp=1451606400&to_timestamp=1735109774&for_update=false&currency=usd&is_inverted=false
    """
    endpoint = f"{GECKO_TERMINAL_CANDLESTICKS_ENDPOINT}/{pool_id}/{pair_id}"
    current_timestamp = str(int(time.time()))
    current_date = datetime.datetime.now(datetime.timezone.utc)
    count_back = str(int((current_date - PUMPFUN_LAUNCH_DATE).total_seconds() // 3600))
    params = {
        "resolution": "60",
        "from_timestamp": PUMPFUN_LAUNCH_DATE_TIMESTAMP,
        "to_timestamp": current_timestamp,
        "for_update": "false",
        "count_back": count_back,
        "currency": "usd",
        "is_inverted": "false",
    }

    response = APIRequest(GECKO_TERMINAL_BASE_URL).get(endpoint, params)

    if response.error:
        logger.error(f"Failed to retrieve OHLC data: {response.error}")
        return CandleData.default()

    body = response.to_dict().get("body")

    if body is None:
        logger.error("Failed to retrieve OHLC data: response body is empty")
        return CandleData.default()

    return CandleData.from_dict(body)
