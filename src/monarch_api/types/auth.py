from __future__ import annotations

from dataclasses import dataclass

from monarch_api.types.common import JsonDict


@dataclass(slots=True)
class AuthSession:
    token: str
    token_expiration: str | None = None
    user_id: str | None = None
    email: str | None = None

    @classmethod
    def from_login_response(cls, data: JsonDict) -> AuthSession:
        token = data.get("token")
        if not isinstance(token, str) or not token:
            raise ValueError("Login response did not include a session token.")
        return cls(
            token=token,
            token_expiration=data.get("tokenExpiration"),
            user_id=data.get("id"),
            email=data.get("email"),
        )

    @classmethod
    def from_dict(cls, data: JsonDict) -> AuthSession:
        token = data.get("token")
        if not isinstance(token, str) or not token:
            raise ValueError("Saved session did not include a session token.")
        return cls(
            token=token,
            token_expiration=data.get("token_expiration"),
            user_id=data.get("user_id"),
            email=data.get("email"),
        )

    def to_dict(self) -> JsonDict:
        return {
            "token": self.token,
            "token_expiration": self.token_expiration,
            "user_id": self.user_id,
            "email": self.email,
        }
