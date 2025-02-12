import http.client
import json
from types import TracebackType
from typing import Any, Dict, Optional, Type, Union
from urllib.parse import urlencode


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
        _ = exc_type, exc_val, exc_tb

        self.close()
        self.close()

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str]:
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
            result = self._handle_response(response)
        except Exception as err:
            result = {"error": str(err)}
        return result

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str]:
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str]:
        return self.request(
            "POST", endpoint, data=data, json_data=json_data, headers=headers
        )

    def put(
        self,
        endpoint: str,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str]:
        return self.request(
            "PUT", endpoint, data=data, json_data=json_data, headers=headers
        )

    def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], str]:
        return self.request("DELETE", endpoint, headers=headers)

    def _handle_response(
        self, response: http.client.HTTPResponse
    ) -> Union[Dict[str, Any], str]:
        try:
            content = response.read().decode()
        except Exception as err:
            return {"error": f"Error reading response: {err}"}

        if response.status >= 400:
            return {
                "error": response.reason,
                "status_code": response.status,
                "body": content,
            }

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Return raw result if JSON decoding fails.
            return content

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
