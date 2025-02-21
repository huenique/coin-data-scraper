import sys
from typing import List, Optional

from sqlalchemy.orm import Session

from coin_data.db.schema import Coin, MarketCapHistory, SessionLocal


def get_market_cap(session: Session, contract_address: str) -> None:
    coin: Optional[Coin] = (
        session.query(Coin).filter(Coin.contract_address == contract_address).first()
    )
    if not coin:
        print("Coin not found.")
        return

    print(f"Coin: {coin.name} ({coin.ticker})")
    print(
        f"Highest Market Cap: {coin.highest_market_cap} at {coin.highest_market_cap_relative_time}"
    )
    print(
        f"Lowest Market Cap: {coin.lowest_market_cap} at {coin.lowest_market_cap_relative_time}"
    )

    caps: List[MarketCapHistory] = (
        session.query(MarketCapHistory)
        .filter(MarketCapHistory.coin_id == coin.id)
        .all()
    )
    print("\nMarket Cap History:")
    for entry in caps:
        print(f"{entry.relative_time} → {entry.market_cap}")


if __name__ == "__main__":
    # Smoke test

    if len(sys.argv) != 2:
        print("Usage: python get_market_cap.py <contract_address>")
        sys.exit(1)

    contract_address: str = sys.argv[1]

    with SessionLocal() as session:
        get_market_cap(session, contract_address)
