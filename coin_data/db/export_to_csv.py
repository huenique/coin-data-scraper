from typing import List

import pandas as pd
from sqlalchemy import Column
from sqlalchemy.orm import Session

from coin_data.db.schema import Coin, SessionLocal


def export_to_csv(session: Session, filename: str = "coins_data.csv") -> None:
    coins: List[Coin] = session.query(Coin).all()

    data: list[dict[str, Column[str] | str]] = [
        {
            "name": coin.name,
            "ticker": coin.ticker,
            "contract_address": coin.contract_address,
            "platform": coin.platform,
            "date_created": str(coin.date_created),
            "highest_market_cap": str(coin.highest_market_cap),
            "highest_market_cap_relative_time": str(
                coin.highest_market_cap_relative_time
            ),
            "lowest_market_cap": str(coin.lowest_market_cap),
            "lowest_market_cap_relative_time": str(
                coin.lowest_market_cap_relative_time
            ),
        }
        for coin in coins
    ]

    df: pd.DataFrame = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Exported to {filename}")


if __name__ == "__main__":
    with SessionLocal() as session:
        export_to_csv(session)
