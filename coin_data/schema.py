from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///coins.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Coin(Base):
    __tablename__ = "coins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    contract_address = Column(String(255), unique=True, nullable=False)
    picture_url = Column(Text)
    ticker = Column(String(50))
    telegram = Column(Text)
    twitter = Column(Text)
    website = Column(Text)
    platform = Column(String(100))
    date_created = Column(TIMESTAMP)

    highest_market_cap: Column[Numeric[float]] = Column(Numeric)
    highest_market_cap_relative_time = Column(String)
    lowest_market_cap: Column[Numeric[float]] = Column(Numeric)
    lowest_market_cap_relative_time = Column(String)

    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    market_caps = relationship(
        "MarketCapHistory", back_populates="coin", cascade="all, delete"
    )


class MarketCapHistory(Base):
    __tablename__ = "market_cap_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"))
    market_cap: Column[Numeric[float]] = Column(Numeric, nullable=False)
    relative_time = Column(String, nullable=False)
    recorded_at = Column(TIMESTAMP, default=func.now())

    coin = relationship("Coin", back_populates="market_caps")


class BondingCurve(Base):
    __tablename__ = "bonding_curve"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False)
    discriminator: Column[Numeric[int]] = Column(Numeric, nullable=False)
    virtual_token_reserves: Column[Numeric[int]] = Column(Numeric, nullable=False)
    virtual_sol_reserves: Column[Numeric[int]] = Column(Numeric, nullable=False)
    real_token_reserves: Column[Numeric[int]] = Column(Numeric, nullable=False)
    real_sol_reserves: Column[Numeric[int]] = Column(Numeric, nullable=False)
    token_total_supply: Column[Numeric[int]] = Column(Numeric, nullable=False)
    complete = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())


Base.metadata.create_all(engine)
