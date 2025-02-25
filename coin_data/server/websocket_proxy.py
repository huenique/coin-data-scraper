import asyncio
from typing import Any, Set

import picologging as logging
import socketio
from litestar import WebSocket, websocket
from litestar.datastructures import State
from socketio.exceptions import ConnectionError

from coin_data.server.constants import HEADERS, UPSTREAM_WEBSOCKET_URL

logger = logging.getLogger(__name__)


sio = socketio.AsyncClient(
    reconnection=True,  # Enable automatic reconnect
    reconnection_attempts=100,  # Try up to 100 times before failing
    reconnection_delay=1,  # Start with a 1s delay
    reconnection_delay_max=60,  # Cap delay at 60s
)

connected_clients: Set[WebSocket[None, None, State]] = set()


async def connect_to_socketio_server():
    """Connect to the upstream Socket.IO WebSocket server."""
    delay = 1
    max_delay = 60

    while True:
        try:
            await sio.connect(  # type: ignore
                f"{UPSTREAM_WEBSOCKET_URL}",
                headers=HEADERS,
                transports=["websocket"],
                socketio_path="/socket.io/",
            )

            logger.info("Connected to upstream WebSocket.")

            delay = 1

            await sio.wait()  # type: ignore

        except ConnectionError as e:
            logger.error(f"Connection lost: {e}. Retrying in {delay} seconds...")

        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying in {delay} seconds...")

        await asyncio.sleep(delay)

        delay = min(delay * 2, max_delay)  # Exponential backoff


@sio.on("*")  # type: ignore
async def handle_socketio_event(event: Any, data: Any):
    """Handles all events from the upstream Socket.IO WebSocket server."""
    logger.debug(f"Received event: {event}")

    for client in connected_clients:
        try:
            await client.send_json({"event": event, "data": data})
        except Exception as e:
            print(f"Error sending to client: {e}")


@websocket("/ws")
async def websocket_proxy(socket: WebSocket[None, None, State]) -> None:
    """Handle WebSocket client connections."""
    await socket.accept()
    connected_clients.add(socket)

    try:
        while True:
            await socket.receive_text()  # Clients may send messages (optional)
    except Exception:
        pass
    finally:
        connected_clients.remove(socket)


# Start the Socket.IO connection in the background
asyncio.create_task(connect_to_socketio_server())
