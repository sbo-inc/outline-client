import json
import os
from typing import Any, cast

from outline_client.client import OutlineClient

# =============================================================================
# CLASS: ClientContext
# =============================================================================


class ClientContext:
    """
    Lazy client holder attached to the Click context object.
    """

    def __init__(self, log: bool = False) -> None:
        self._log = log
        self._client: OutlineClient | None = None

    @property
    def client(self) -> OutlineClient:
        """
        Construct the underlying client on first access.

        Connection and credential settings are sourced from the standard
        `OUTLINE_API_*` environment variables. Extra request headers may be
        supplied as a JSON object in `OUTLINE_API_HEADERS` (e.g. to
        authenticate through a proxy that fronts the API).
        `OUTLINE_API_TIMEOUT` (seconds) and `OUTLINE_API_RETRIES`
        (connection-retry count) override the client defaults for unattended
        runs.
        """
        if self._client is None:
            raw = os.environ.get("OUTLINE_API_HEADERS")
            headers: dict[str, str] = (
                cast(dict[str, Any], json.loads(raw)) if raw else {}
            )

            kwargs: dict[str, Any] = {}
            timeout = os.environ.get("OUTLINE_API_TIMEOUT")
            if timeout:
                kwargs["timeout"] = float(timeout)
            retries = os.environ.get("OUTLINE_API_RETRIES")
            if retries:
                kwargs["retries"] = int(retries)

            self._client = OutlineClient(log=self._log, headers=headers, **kwargs)

        return self._client
