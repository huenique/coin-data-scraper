import http.client
import json
import random
import ssl
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from types import TracebackType
from typing import Any, Optional, Type
from urllib.parse import urlparse

from python_socks.sync import Proxy

from coin_data.config import PROXIES_ENABLED
from coin_data.logging import logger
from coin_data.proxies import PROXIES

ENDPOINT_PREFIX = "/"
HEADER_CONTENT_TYPE = "Content-Type"
JSON_CONTENT_TYPE = "application/json"
HTTP_ERROR_FORMAT = "HTTP {status_code} Error"
MAX_PROXY_RETRIES = 3


def build_url(endpoint: str, params: list[tuple[str, str]] | None = None) -> str:
    """Constructs a URL with the given endpoint and query parameters."""
    url = f"/{endpoint}"

    if params:
        query_parts: list[str] = [f"{key}={value}" for key, value in params]
        url += "?" + "&".join(query_parts)

    return url


def build_headers(headers: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Creates a copy of header dict or returns an empty one."""
    return headers.copy() if headers else {}


class JSONConvertible(ABC):
    @abstractmethod
    def to_json(self) -> str:
        pass


class StatusRaisable(ABC):
    @abstractmethod
    def raise_for_status(self) -> None:
        pass


@dataclass
class APIResponse(JSONConvertible, StatusRaisable):
    status_code: int
    error: Optional[str] = None
    body: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            msg = self.error or HTTP_ERROR_FORMAT.format(status_code=self.status_code)
            raise Exception(msg)


class APIRequest:
    def __init__(
        self, base_url: str, use_ssl: bool = True, timeout: Optional[int] = None
    ) -> None:
        self.base_url: str = base_url
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.proxy_index = None
        self.conn = None
        self.dead_proxies: set[str] = set()

        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize connection, selecting a proxy if enabled and available."""

        # Ensure base_url has a scheme
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"https://{self.base_url}"

        valid_proxies = [proxy.strip() for proxy in PROXIES if proxy and proxy.strip()]

        if PROXIES_ENABLED and valid_proxies:
            self.use_proxy = True
            self.proxy_index = random.randint(0, len(valid_proxies) - 1)
            try:
                self._connect_via_proxy(self.proxy_index, valid_proxies)
            except ValueError as e:
                logger.warning(
                    f"Proxy initialization failed: {e}. Using direct connection."
                )
                self.use_proxy = False
                self._connect_direct()
        else:
            logger.debug("No valid proxies available. Using direct connection.")
            self.use_proxy = False
            self._connect_direct()

    def _connect_direct(self) -> None:
        """Establish a direct connection (without a proxy)."""

        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"https://{self.base_url}"

        parsed_url = urlparse(self.base_url)

        if not parsed_url.hostname:
            raise ValueError(f"Invalid base URL after fix: {self.base_url}")

        host = parsed_url.hostname
        port = parsed_url.port or (443 if self.use_ssl else 80)

        logger.debug(f"Using d`irect connection to {host}:{port}")

        conn_class = (
            http.client.HTTPSConnection if self.use_ssl else http.client.HTTPConnection
        )

        self.conn = conn_class(host, port=port, timeout=self.timeout)
        self.proxy_host = None
        self.proxy_port = None

    def _connect_via_proxy(self, index: int, valid_proxies: list[str]) -> None:
        """Establish a connection using a proxy and attach it to self.conn."""

        if not self.use_proxy:
            self._connect_direct()
            return

        proxy = valid_proxies[index]

        if not proxy:
            self._connect_direct()
            return

        # Fix: Convert `socks5h://` to `socks5://` for compatibility
        if proxy.startswith("socks5h://"):
            proxy = proxy.replace("socks5h://", "socks5://", 1)

        logger.debug(f"Using Proxy: {proxy}")

        parsed_proxy = urlparse(proxy)
        proxy_host = parsed_proxy.hostname
        proxy_port = parsed_proxy.port

        if not proxy_host or not proxy_port:
            logger.warning(f"Invalid proxy format: {proxy}. Using direct connection.")
            self.use_proxy = False
            self._connect_direct()
            return

        # Extract only the hostname for connection
        parsed_base_url = urlparse(self.base_url)
        dest_host = parsed_base_url.hostname
        dest_port = parsed_base_url.port or (443 if self.use_ssl else 80)

        if not dest_host:
            raise ValueError(f"Invalid base URL: {self.base_url}")

        proxy_client = Proxy.from_url(proxy, rdns=True)  # type: ignore
        raw_sock = None

        try:
            raw_sock = proxy_client.connect(dest_host=dest_host, dest_port=dest_port)
        except Exception as e:
            logger.debug(
                f"Proxy {proxy_host}:{proxy_port} failed. Retrying another proxy. Error: {e}"
            )

            # Mark this proxy as dead
            self.dead_proxies.add(valid_proxies[index])

            if not self._retry_with_other_proxies(index):
                return

        if self.use_ssl and raw_sock:
            raw_sock = ssl.create_default_context().wrap_socket(
                raw_sock, server_hostname=dest_host
            )

        conn_class = (
            http.client.HTTPSConnection if self.use_ssl else http.client.HTTPConnection
        )

        self.conn = conn_class(dest_host, timeout=self.timeout)
        self.conn.sock = raw_sock
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def _retry_with_other_proxies(self, failed_index: int) -> bool:
        """
        Attempt to reconnect using the **same proxy first** before switching to others.
        If a proxy fails too many times, it is permanently blacklisted.
        Returns True if a new proxy is set, False if all proxies fail.
        """
        valid_proxies = [proxy.strip() for proxy in PROXIES if proxy and proxy.strip()]

        if not valid_proxies:
            logger.warning(
                "No valid proxies available. Falling back to direct connection."
            )
            self.use_proxy = False

            # Ensure `self.conn` is set
            self._connect_direct()

            return False

        proxy_to_retry = valid_proxies[failed_index]

        # Immediately skip dead proxies
        if proxy_to_retry in self.dead_proxies:
            logger.debug(f"Skipping dead proxy: {proxy_to_retry}")
            return self._switch_to_next_proxy(failed_index, valid_proxies)

        for attempt in range(MAX_PROXY_RETRIES):
            try:
                logger.info(
                    f"Retrying same proxy ({attempt + 1}/{MAX_PROXY_RETRIES}): {proxy_to_retry}"
                )

                # If the proxy is already dead, don't retry it
                if proxy_to_retry in self.dead_proxies:
                    logger.debug(f"Skipping dead proxy: {proxy_to_retry}")
                    return self._switch_to_next_proxy(failed_index, valid_proxies)

                # Reinitialize failed proxy
                self._connect_via_proxy(failed_index, valid_proxies)
                self.proxy_index = failed_index
                return True
            except Exception as e:
                logger.warning(
                    f"Proxy {proxy_to_retry} failed on retry {attempt + 1}: {e}"
                )

        # Mark this proxy as dead and never retry it again
        logger.error(
            f"Proxy {proxy_to_retry} is unreachable after {MAX_PROXY_RETRIES} attempts. Skipping permanently."
        )
        self.dead_proxies.add(proxy_to_retry)

        return self._switch_to_next_proxy(failed_index, valid_proxies)

    def _switch_to_next_proxy(
        self, failed_index: int, valid_proxies: list[str]
    ) -> bool:
        """Switch to the next available proxy, skipping dead proxies."""
        ordered_indices = list(range(len(valid_proxies)))

        # Skip the already-failed proxy
        ordered_indices.remove(failed_index)

        for index in ordered_indices:
            proxy_to_try = valid_proxies[index]

            # Don't retry dead proxies
            if proxy_to_try in self.dead_proxies:
                logger.error(f"Skipping dead proxy: {proxy_to_try}")
                continue

            try:
                logger.info(f"Switching to new proxy: {proxy_to_try}")
                self._connect_via_proxy(index, valid_proxies)
                self.proxy_index = index
                return True
            except Exception as e:
                logger.warning(f"Proxy {proxy_to_try} failed: {e}")

                # Try the next proxy
                continue

        logger.debug("All proxies failed. Using direct connection.")
        self.use_proxy = False
        self._connect_direct()
        return False

    def __enter__(self) -> "APIRequest":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[list[tuple[str, str]]] = None,
        data: Optional[str] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> APIResponse:
        if self.conn is None:
            raise ValueError("Connection is not initialized")

        url = build_url(endpoint, params)
        req_headers = build_headers(headers)
        body = json.dumps(json_data) if json_data else data

        if json_data and HEADER_CONTENT_TYPE not in req_headers:
            req_headers[HEADER_CONTENT_TYPE] = JSON_CONTENT_TYPE

        attempt = 0
        max_attempts = len(PROXIES) if PROXIES_ENABLED else 1

        parsed_base_url = urlparse(self.base_url)
        host = parsed_base_url.hostname or ""

        while attempt < max_attempts:
            try:
                if PROXIES_ENABLED:
                    logger.debug(f"Using proxy: {self.proxy_host}:{self.proxy_port}")

                    if self.proxy_host and self.proxy_host.startswith("http"):
                        self.conn.set_tunnel(host)

                self.conn.request(method, url, body=body, headers=req_headers)
                response = self.conn.getresponse()
                return self._handle_response(response)
            except (ConnectionRefusedError, TimeoutError, OSError) as err:
                logger.warning(
                    f"Proxy {self.proxy_host}:{self.proxy_port} failed: {err}"
                )

                if PROXIES_ENABLED and self.proxy_index is not None:
                    if not self._retry_with_other_proxies(self.proxy_index):
                        return APIResponse(
                            status_code=0, error="All proxies failed", body=None
                        )
                else:
                    return APIResponse(status_code=0, error=str(err), body=None)

            attempt += 1

        return APIResponse(status_code=0, error="All proxies failed", body=None)

    def get(
        self,
        endpoint: str,
        params: Optional[list[tuple[str, str]]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> APIResponse:
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> APIResponse:
        return self.request(
            "POST", endpoint, data=data, json_data=json_data, headers=headers
        )

    def put(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> APIResponse:
        return self.request(
            "PUT", endpoint, data=data, json_data=json_data, headers=headers
        )

    def delete(
        self, endpoint: str, headers: Optional[dict[str, str]] = None
    ) -> APIResponse:
        return self.request("DELETE", endpoint, headers=headers)

    def _handle_response(self, response: http.client.HTTPResponse) -> APIResponse:
        try:
            content = response.read().decode()
        except Exception as err:
            return APIResponse(
                status_code=response.status,
                error=f"Error reading response: {err}",
                body=None,
            )

        if response.status >= 400:
            return APIResponse(
                status_code=response.status,
                error=response.reason,
                body=content,
            )

        try:
            data = json.loads(content)
            return APIResponse(
                status_code=response.status,
                body=data,
            )
        except json.JSONDecodeError:
            return APIResponse(
                status_code=response.status,
                body=content,
            )

    def close(self) -> None:
        if not self.conn:
            return

        try:
            self.conn.close()
        except Exception:
            pass
