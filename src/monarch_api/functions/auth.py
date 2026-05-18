from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from monarch_api.functions.common import (
    API_BASE_URL,
    MfaRequiredError,
    MonarchAuthError,
    build_auth_headers,
    parse_error,
)
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict


def create_session(
    email: str,
    password: str,
    *,
    mfa_code: str | None = None,
    trusted_device: bool = True,
    session_path: str | Path | None = None,
) -> AuthSession:
    payload: JsonDict = {
        "username": email,
        "password": password,
        "trusted_device": trusted_device,
        "supports_mfa": True,
    }
    if mfa_code:
        payload["totp"] = mfa_code

    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        response = client.post(
            "/auth/login/",
            json=payload,
            headers=build_auth_headers(),
        )

    data = _response_json(response)
    if response.status_code == 200:
        session = AuthSession.from_login_response(data)
        if session_path is not None:
            save_session(session, session_path)
        return session

    error_code = data.get("error_code")
    if error_code == "MFA_REQUIRED":
        raise MfaRequiredError("MFA is required. Call create_session again with mfa_code.")

    raise MonarchAuthError(parse_error(data))


def save_session(session: AuthSession, path: str | Path) -> None:
    session_path = Path(path)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")


def load_session(path: str | Path) -> AuthSession:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Saved session file must contain a JSON object.")
    return AuthSession.from_dict(data)


def _response_json(response: httpx.Response) -> JsonDict:
    data: Any = response.json()
    if not isinstance(data, dict):
        raise MonarchAuthError("Monarch auth response was not a JSON object.")
    return data
