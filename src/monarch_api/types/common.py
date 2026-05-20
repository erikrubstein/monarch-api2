from __future__ import annotations

from dataclasses import dataclass
from typing import Any

JsonDict = dict[str, Any]


@dataclass(slots=True)
class User:
    id: str
    display_name: str | None = None
    profile_picture_url: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> User | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            display_name=data.get("displayName") or data.get("name"),
            profile_picture_url=data.get("profilePictureUrl"),
            raw=dict(data),
        )
