import datetime
import json
from typing import Any, Dict

from schema import Coin, MarketCapHistory, SessionLocal
from sqlalchemy.orm import Session


def insert_coin(session: Session, coin_data: Dict[str, Any]) -> None:
    coin = Coin(
        name=coin_data["name"],
        contract_address=coin_data["contract_address"],
        picture_url=coin_data.get("picture_url"),
        ticker=coin_data.get("ticker"),
        telegram=coin_data.get("telegram"),
        twitter=coin_data.get("twitter"),
        website=coin_data.get("website"),
        platform=coin_data.get("platform"),
        date_created=datetime.datetime.fromisoformat(coin_data["date_created"]),
        highest_market_cap=coin_data.get("highest_market_cap"),
        highest_market_cap_relative_time=coin_data.get(
            "highest_market_cap_relative_time"
        ),
        lowest_market_cap=coin_data.get("lowest_market_cap"),
        lowest_market_cap_relative_time=coin_data.get(
            "lowest_market_cap_relative_time"
        ),
    )

    session.add(coin)
    session.commit()

    for entry in coin_data.get("market_caps", []):
        market_cap_record = MarketCapHistory(
            coin_id=coin.id,
            market_cap=entry["value"],
            relative_time=entry["relative_time"],
        )
        session.add(market_cap_record)

    session.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        with open("scraped_data.json", "r") as f:
            data: Dict[str, Any] = json.load(f)
            insert_coin(session, data)
