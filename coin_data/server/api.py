from pathlib import Path

import picologging as logging
from litestar import Litestar, Response, get

from coin_data.server.contracts import get_contracts_batch
from coin_data.server.health import health_check
from coin_data.server.home import home
from coin_data.server.logger import CustomLoggingConfig
from coin_data.server.twitter_api import get_twitter_data
from coin_data.server.websocket_proxy import websocket_proxy

logger = logging.getLogger(__name__)
favicon_path = Path(__file__).parent / "static" / "favicon.ico"


@get("/favicon.ico")
async def get_favicon() -> Response[bytes]:
    """Serve a default favicon to prevent 404 errors."""
    if favicon_path.exists():
        return Response(content=favicon_path.read_bytes(), media_type="image/x-icon")
    return Response(content=b"", media_type="image/x-icon")  # Empty response


app = Litestar(
    route_handlers=[
        home,
        health_check,
        get_contracts_batch,
        websocket_proxy,
        get_twitter_data,
    ],
    logging_config=CustomLoggingConfig(),
)


for route in app.routes:
    logger.info(f"Registered route: {route.path}")
