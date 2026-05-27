import json
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import ENOVACOM_BASE_URL, require_token


class EnovacomError(Exception):
    pass


class EnovacomClient:
    def __init__(self) -> None:
        self._config_cache: Optional[dict[str, Any]] = None

    def call(self, command: str, **params: Any) -> dict[str, Any]:
        body = {
            "token": require_token(),
            "command": command,
            **params,
        }
        data = json.dumps(body).encode("utf-8")
        request = Request(
            ENOVACOM_BASE_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise EnovacomError(f"Enovacom HTTP error: {error.code} - {details}") from error
        except URLError as error:
            raise EnovacomError(f"Enovacom connection error: {error.reason}") from error

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise EnovacomError("Enovacom returned invalid JSON") from error

        if not isinstance(parsed, dict):
            raise EnovacomError("Enovacom returned an unexpected response")

        return parsed

    def get_config(self) -> dict[str, Any]:
        if self._config_cache is None:
            self._config_cache = self.call("get_config")
        return self._config_cache


client = EnovacomClient()
