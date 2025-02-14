import http.client
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from types import TracebackType
from typing import Any, Optional, Type

ENDPOINT_PREFIX = "/"
HEADER_CONTENT_TYPE = "Content-Type"
JSON_CONTENT_TYPE = "application/json"
HTTP_ERROR_FORMAT = "HTTP {status_code} Error"


def build_url(endpoint: str, params: dict[str, str] | None = None) -> str:
    """Constructs a URL with the given endpoint and query parameters."""
    url = f"/{endpoint}"
    if params:
        # Handle lists properly for repeated keys
        query_parts: list[str] = []
        for key, value in params.items():
            if isinstance(value, list):
                for v in value:
                    query_parts.append(f"{key}={v}")
            else:
                query_parts.append(f"{key}={value}")
        url += "?" + "&".join(query_parts)
    return url


def build_headers(headers: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Creates a copy of header dict or returns an empty one."""
    return headers.copy() if headers else {}


class JSONConvertible(ABC):
    @abstractmethod
    def to_json(self) -> str:
        """
        Convert the instance to a JSON string.
        External modules can implement this interface to provide custom JSON conversion.
        """
        pass


class StatusRaisable(ABC):
    @abstractmethod
    def raise_for_status(self) -> None:
        """
        Raise an exception if the status code indicates an error.
        """
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
        conn_class = (
            http.client.HTTPSConnection if use_ssl else http.client.HTTPConnection
        )
        self.base_url: str = base_url
        self.conn: http.client.HTTPSConnection | http.client.HTTPConnection = (
            conn_class(base_url, timeout=timeout)
        )

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
        params: Optional[dict[str, str]] = None,
        data: Optional[str] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> APIResponse:
        url = build_url(endpoint, params=params)
        req_headers = build_headers(headers)
        body = None

        if json_data:
            body = json.dumps(json_data)
            if HEADER_CONTENT_TYPE not in req_headers:
                req_headers[HEADER_CONTENT_TYPE] = JSON_CONTENT_TYPE
        elif data:
            body = data

        try:
            self.conn.request(method, url, body=body, headers=req_headers)
            response = self.conn.getresponse()
            return self._handle_response(response)
        except Exception as err:
            return APIResponse(
                status_code=0,
                error=str(err),
                body=None,
            )

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, str]] = None,
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
            # Return raw response if JSON decoding fails.
            return APIResponse(
                status_code=response.status,
                body=content,
            )

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
