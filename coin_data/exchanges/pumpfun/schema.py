from dataclasses import dataclass


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
    mint: str
    image_uri: str
    symbol: str
    telegram: str
    twitter: str
    website: str
    created_timestamp: str
    raydium_pool: str
    virtual_sol_reserves: int
    virtual_token_reserves: int
    total_supply: int
    highest_market_cap: int
    highest_market_cap_timestamp: int
    lowest_market_cap: int
    lowest_market_cap_timestamp: int
    current_market_cap: int
    current_market_cap_timestamp: int
    holder_count: str
