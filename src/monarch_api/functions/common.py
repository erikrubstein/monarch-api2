from __future__ import annotations

from uuid import uuid4

from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict

API_BASE_URL = "https://api.monarch.com"
CLIENT_VERSION = "v1.0.2079"


class MonarchError(Exception):
    pass


class MonarchAuthError(MonarchError):
    pass


class MfaRequiredError(MonarchAuthError):
    pass


def build_auth_headers(
    session: AuthSession | None = None,
    *,
    graphql: bool = False,
) -> dict[str, str]:
    headers = {
        "Accept": "*" if graphql else "application/json",
        "Client-Platform": "web",
        "Device-UUID": str(uuid4()),
        "Monarch-Client": (
            "monarch-core-web-app-graphql"
            if graphql
            else "monarch-core-web-app-rest"
        ),
        "Monarch-Client-Version": CLIENT_VERSION,
        "Origin": "https://app.monarch.com",
        "User-Agent": "monarch-api2/0.1.0",
    }
    if session is not None:
        headers["Authorization"] = f"Token {session.token}"
    return headers


def parse_error(data: JsonDict) -> str:
    return str(data.get("detail") or data.get("message") or "Monarch request failed.")
