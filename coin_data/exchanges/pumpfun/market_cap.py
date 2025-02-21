from dataclasses import dataclass
from datetime import datetime
from typing import Any

from coin_data.exchanges.common import DefaultMixin
from coin_data.exchanges.pumpfun.constants import (
    GECKO_TERMINAL_BASE_URL,
    GECKO_TERMINAL_POOLS_ENDPOINT,
)
from coin_data.exchanges.pumpfun.ohlc import CandleData
from coin_data.logging import logger
from coin_data.requests import APIRequest

RelationshipData = dict[str, Any]


@dataclass
class TokenReserve(DefaultMixin):
    reserves: str
    reserves_in_usd: float


@dataclass
class TokenValueData(DefaultMixin):
    fdv_in_usd: float
    market_cap_in_usd: float
    market_cap_to_holders_ratio: float


@dataclass
class HistoricalDataEntry(DefaultMixin):
    swaps_count: int
    buyers_count: int
    price_in_usd: str
    sellers_count: int
    volume_in_usd: str
    buy_swaps_count: int
    sell_swaps_count: int


@dataclass
class LockedLiquidity(DefaultMixin):
    locked_percent: float
    next_unlock_percent: float | None
    next_unlock_timestamp: int | None
    final_unlock_timestamp: int | None
    updated_at: int
    source: str
    url: str


@dataclass
class GTScoreDetails(DefaultMixin):
    info: float
    pool: float
    transactions: float
    holders: float
    creation: float


@dataclass
class HighLowPriceData(DefaultMixin):
    high_price_in_usd_24h: float
    high_price_timestamp_24h: str
    low_price_in_usd_24h: float
    low_price_timestamp_24h: str


@dataclass
class PoolAttributes(DefaultMixin):
    address: str
    name: str
    fully_diluted_valuation: str
    base_token_id: str
    price_in_usd: str
    price_in_target_token: str
    reserve_in_usd: str
    reserve_threshold_met: bool
    from_volume_in_usd: str
    to_volume_in_usd: str
    api_address: str
    pool_fee: float | None
    token_weightages: dict[str, float] | None
    token_reserves: dict[str, TokenReserve]
    token_value_data: dict[str, TokenValueData]
    balancer_pool_id: str | None
    swap_count_24h: int
    swap_url: str
    sentiment_votes: dict[str, float]
    price_percent_change: str
    price_percent_changes: dict[str, str]
    historical_data: dict[str, HistoricalDataEntry]
    locked_liquidity: LockedLiquidity
    security_indicators: list[str]
    gt_score: float
    gt_score_details: GTScoreDetails
    pool_reports_count: int
    pool_created_at: str
    latest_swap_timestamp: str
    high_low_price_data_by_token_id: dict[str, HighLowPriceData]
    is_nsfw: bool
    is_stale_pool: bool | None
    is_pool_address_explorable: bool
    suggested_pools_by_liquidity: Any | None = None


@dataclass
class Relationships(DefaultMixin):
    dex: dict[str, RelationshipData]
    tokens: list[RelationshipData]
    pool_metric: dict[str, RelationshipData]
    pairs: dict[Any, list[RelationshipData]]


@dataclass
class PoolData(DefaultMixin):
    id: str
    type: str
    attributes: PoolAttributes
    relationships: Relationships | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PoolData":
        data_item = data.get("data", {})
        if not data_item or isinstance(data_item, list):
            logger.warning("No 'data' field found in the input dictionary.")
            return cls.default()

        attributes_data = data_item.get("attributes", {})
        relationships_data = data_item.get("relationships", {})

        try:
            pool_attributes = PoolAttributes(**attributes_data)
        except TypeError as e:
            logger.error(f"Failed to initialize PoolAttributes: {e}")
            pool_attributes = PoolAttributes.default()

        try:
            relationships = Relationships(**relationships_data)
        except TypeError as e:
            logger.error(f"Failed to initialize Relationships: {e}")
            relationships = Relationships.default()

        return cls(
            id=data_item.get("id", "default_id"),
            type=data_item.get("type", "default_type"),
            attributes=pool_attributes,
            relationships=relationships,
        )


@dataclass
class IncludedData(DefaultMixin):
    id: str
    type: str
    attributes: dict[str, Any]
    relationships: dict[Any, Any]


@dataclass
class ResponseData(DefaultMixin):
    data: PoolData | None
    included: list[IncludedData] | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResponseData":
        return cls(
            data=PoolData.from_dict(data),
            included=[IncludedData(**item) for item in data.get("included", [])],
        )


def get_token_data(token_address: str) -> ResponseData:
    """
    https://app.geckoterminal.com/api/p1/solana/pools/{token_address | raydium_pool}?include=tokens.tags&base_token=0
    """
    endpoint = f"{GECKO_TERMINAL_POOLS_ENDPOINT}/{token_address}"
    params = [("include", "tokens.tags"), ("base_token", "0")]
    response = APIRequest(GECKO_TERMINAL_BASE_URL).get(endpoint, params)

    if response.error:
        logger.error(f"Failed to retrieve token data: {response.error}")
        return ResponseData.default()

    return ResponseData.from_dict(response.to_dict()["body"])


def get_relative_time(creation_time: str, event_time: str) -> str:
    creation_dt = datetime.fromisoformat(creation_time)
    event_dt = datetime.fromisoformat(event_time)
    delta = event_dt - creation_dt
    return f"+{str(delta)}"


def get_market_cap_with_times(
    ohlc: CandleData, circulating_supply: float
) -> dict[str, Any]:
    if not ohlc.data:
        return {}

    creation_time = ohlc.data[0].dt

    highest_candle = max(ohlc.data, key=lambda x: x.h)
    highest_market_cap = round(highest_candle.h * circulating_supply, 2)
    highest_time = get_relative_time(creation_time, highest_candle.dt)

    lowest_candle = min(ohlc.data, key=lambda x: x.l)
    lowest_market_cap = round(lowest_candle.l * circulating_supply, 2)
    lowest_time = get_relative_time(creation_time, lowest_candle.dt)

    current_candle = ohlc.data[-1]
    current_market_cap = round(current_candle.c * circulating_supply, 2)
    current_time = get_relative_time(creation_time, current_candle.dt)

    return {
        "highest_market_cap": highest_market_cap,
        "highest_market_cap_time": highest_time,
        "lowest_market_cap": lowest_market_cap,
        "lowest_market_cap_time": lowest_time,
        "current_market_cap": current_market_cap,
        "current_market_cap_time": current_time,
    }
