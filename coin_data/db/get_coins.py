from typing import List

from sqlalchemy.orm import Session

from coin_data.db.schema import Coin, SessionLocal


def get_all_coins(session: Session) -> None:
    coins: List[Coin] = session.query(Coin).all()
    for coin in coins:
        print(
            f"{coin.name} ({coin.ticker}) - Platform: {coin.platform}, Created: {coin.date_created}"
        )


if __name__ == "__main__":
    with SessionLocal() as session:
        get_all_coins(session)
