import asyncio
import logging
import random
from typing import Any, Awaitable, Callable, List, Union

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebSocketStream:
    def __init__(self) -> None:
        self.subscribers: List[Callable[[str], Union[None, Awaitable[Any]]]] = []

    def subscribe(self, callback: Callable[[str], Union[None, Awaitable[Any]]]) -> None:
        self.subscribers.append(callback)

    async def notify_subscribers(self, message: str) -> None:
        """Notify each subscriber, awaiting if needed."""
        for subscriber in self.subscribers:
            result = subscriber(message)
            if asyncio.iscoroutine(result):
                await result

    async def _receive_and_process(self, websocket: ClientConnection) -> None:
        """Asynchronously iterates through messages and notifies subscribers."""
        async for data in websocket:
            message: str = self._decode_message(data)
            await self.notify_subscribers(message)

    def _decode_message(self, data: Union[str, bytes, bytearray, memoryview]) -> str:
        """Decodes the received data into a string."""
        if isinstance(data, str):
            return data
        elif isinstance(data, (bytes, bytearray)):
            return data.decode("utf-8")
        return data.tobytes().decode("utf-8")

    async def connect(self, uri: str, max_retries: int = 5) -> None:
        """Connects to the WebSocket URI with retry logic."""
        retries: int = 0
        while retries <= max_retries:
            try:
                await self._attempt_connection(uri)
                return  # Successful connection
            except ConnectionClosedError as e:
                logger.warning("Connection closed: %s", e)
                retries += 1
                await self._retry(retries)
            except Exception as e:
                logger.error("An error occurred: %s", e)
                retries += 1
                await self._retry(retries)

        logger.error("Max retries reached. Connection failed.")

    async def _attempt_connection(self, uri: str) -> None:
        """Attempts connection and processes incoming messages."""
        async with websockets.connect(uri) as websocket:
            await self._receive_and_process(websocket)

    async def _retry(self, retries: int) -> None:
        """Calculates delay and awaits before the next retry."""
        delay: float = (2**retries) + random.uniform(0, 1)
        logger.info("Retrying in %.2f seconds...", delay)
        await asyncio.sleep(delay)
