from dataclasses import dataclass, field
from typing import Any


@dataclass
class PriceChange:
    h1: float | None = None
    h24: float | None = None


@dataclass
class TokenInfo:
    chain_id: str
    name: str
    avatar: str | None = None
    description: str | None = None
    creator: str | None = None
    created_at: str | None = None
    market_cap: str | None = None
    volume: str | None = None
    price: str | None = None
    price_change: PriceChange | None = None
    liquidity: str | None = None
    change: dict[str, str] | None = None
    vol: str | None = None
    twitter_link: str | None = None
    website_link: str | None = None
    telegram_link: str | None = None


@dataclass
class Tweet:
    id: str
    text: str
    name: str
    username: str
    likes: int
    retweets: int
    replies: int
    views: int
    time_parsed: str
    is_quoted: bool
    quoted_status: Any | None = None


@dataclass
class ContractData:
    search_results: list[Tweet] = field(default_factory=list)
    token_info: TokenInfo | None = None


@dataclass
class UserData:
    user_not_found: bool
    user_info: Any | None = None
    tweets: Any | None = None
    token_info: TokenInfo | None = None


@dataclass
class AnalysisData:
    user_profile: dict[str, str]


@dataclass
class ForwardedContract:
    contract_address: str
    promotion_count: int
    smart_money_count: int
    signal_type: int
    timestamp: int
    token_info: str
    chain_id: str
    avatar: str | None = None
    description: str | None = None
    creator: str | None = None
    created_at: str | None = None
    market_cap: str | None = None
    volume: str | None = None
    price: str | None = None
    price_change: dict[str, str] | None = None
    liquidity: str | None = None
    twitter: str | None = None
    website: str | None = None
    telegram: str | None = None


@dataclass
class FullResponse:
    event: str
    data: Any  # This can hold different response models like TokenInfo, ContractData, etc.
