from dataclasses import dataclass
from typing import Any


@dataclass
class TotalVolume24h:
    total_volume_24h: int
    total_volume_change_24h: float
    total_trades_24h: int
    total_trades_change_24h: float
    token1: str
    token2: str
    token1_account: str
    token2_account: str
    token1_amount: float
    token2_amount: float
    tvl: float
    create_tx_hash: str | None = None
    create_block_time: int | None = None
    creator: str | None = None


@dataclass
class Volume:
    success: bool
    data: TotalVolume24h
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Volume":
        return cls(
            success=data["success"],
            data=TotalVolume24h(**data["data"]),
            metadata=data["metadata"],
        )


@dataclass
class HolderTotal:
    success: bool
    data: int
    metadata: dict[str, Any]


@dataclass
class Link:
    backward: float
    forward: float
    source: int
    target: int


@dataclass
class Metadata:
    max_amount: int
    min_amount: int


@dataclass
class Holder:
    address: str
    amount: int
    is_contract: bool
    percentage: float
    token_account: str
    transaction_count: int
    ignore: bool | None = False
    is_exchange: bool | None = False
    name: str | None = None

    def __init__(
        self,
        address: str = "",
        amount: int = 0,
        is_contract: bool = False,
        percentage: float = 0.0,
        token_account: str = "",
        transaction_count: int = 0,
    ):
        self.address = address
        self.amount = amount
        self.is_contract = is_contract
        self.percentage = percentage
        self.token_account = token_account
        self.transaction_count = transaction_count


@dataclass
class TokenLink:
    address: str
    decimals: int
    links: list[Link]
    name: str
    symbol: str


@dataclass
class BubbleGraphData:
    chain: str
    dt_update: str
    full_name: str
    id: str
    is_X721: bool
    links: list[Link]
    metadata: Metadata
    nodes: list[Holder]
    source_id: int
    symbol: str
    token_address: str
    token_links: list[TokenLink]
    top_500: bool
    version: int


@dataclass
class Token:
    name: str
    symbol: str
    mint: str
    volume: int
    holder_count: int
    image_uri: str
    telegram: str
    twitter: str
    website: str
    created_timestamp: str
    raydium_pool: str
    highest_market_cap: int
    highest_market_cap_timestamp: int
    lowest_market_cap: int
    lowest_market_cap_timestamp: int
    current_market_cap: int
    current_market_cap_timestamp: int
