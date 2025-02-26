from dataclasses import dataclass

from litestar import get


@dataclass
class HomeResponse:
    message: str


@get("/")
async def home() -> HomeResponse:
    return HomeResponse(message="Welcome to the Coin Data API!")
