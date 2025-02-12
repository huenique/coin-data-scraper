import http.client
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from types import TracebackType
from typing import Any, Dict, Optional, Type, Union
from urllib.parse import urlencode


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
    body: Optional[Any] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(self.error or f"HTTP {self.status_code} Error")


class APIRequest:
    def __init__(
        self, base_url: str, use_ssl: bool = True, timeout: Optional[int] = None
    ) -> None:
        conn_class = (
            http.client.HTTPSConnection if use_ssl else http.client.HTTPConnection
        )
        self.base_url: str = base_url
        self.conn: Union[http.client.HTTPSConnection, http.client.HTTPConnection] = (
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
        params: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        url = f"/{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
        req_headers = headers.copy() if headers else {}
        body = None

        if json_data:
            body = json.dumps(json_data)
            if "Content-Type" not in req_headers:
                req_headers["Content-Type"] = "application/json"
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
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        return self.request(
            "POST", endpoint, data=data, json_data=json_data, headers=headers
        )

    def put(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        return self.request(
            "PUT", endpoint, data=data, json_data=json_data, headers=headers
        )

    def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None
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
