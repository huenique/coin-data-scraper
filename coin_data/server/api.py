from litestar import Litestar

from coin_data.server.contracts import get_contracts_batch
from coin_data.server.health import health_check
from coin_data.server.logger import CustomLoggingConfig
from coin_data.server.twitter_api import get_twitter_data
from coin_data.server.websocket_proxy import websocket_proxy

app = Litestar(
    route_handlers=[
        health_check,
        get_contracts_batch,
        websocket_proxy,
        get_twitter_data,
    ],
    logging_config=CustomLoggingConfig(),
)
