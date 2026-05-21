from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

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


class MonarchGraphQLError(MonarchError):
    pass


def build_auth_headers(
    session: AuthSession | None = None,
    *,
    graphql: bool = False,
) -> dict[str, str]:
    headers = {
        "Accept": "*/*" if graphql else "application/json",
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


def rest_request(
    session: AuthSession,
    method: str,
    path: str,
    *,
    json: JsonDict | None = None,
    graphql: bool = False,
) -> JsonDict:
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        response = client.request(
            method,
            path,
            json=json,
            headers=build_auth_headers(session, graphql=graphql),
        )
    return _parse_response(response)


def graphql_request(
    session: AuthSession,
    operation_name: str,
    query: str,
    variables: JsonDict | None = None,
) -> JsonDict:
    response_data = rest_request(
        session,
        "POST",
        "/graphql",
        json={
            "operationName": operation_name,
            "variables": variables or {},
            "query": query,
        },
        graphql=True,
    )

    errors = response_data.get("errors")
    if errors:
        raise MonarchGraphQLError(str(errors))

    data = response_data.get("data")
    if not isinstance(data, dict):
        raise MonarchGraphQLError("Monarch GraphQL response did not include data.")
    return data


def _parse_response(response: httpx.Response) -> JsonDict:
    data: Any = response.json()
    if not isinstance(data, dict):
        raise MonarchError("Monarch response was not a JSON object.")

    if response.status_code >= 400:
        raise MonarchError(parse_error(data))

    return data
