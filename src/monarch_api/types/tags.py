from __future__ import annotations

from dataclasses import dataclass

from monarch_api.types.common import JsonDict


@dataclass(slots=True)
class Tag:
    id: str
    name: str
    color: str | None = None
    order: int | None = None
    transaction_count: int | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Tag:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            color=data.get("color"),
            order=data.get("order"),
            transaction_count=data.get("transactionCount"),
            raw=dict(data),
        )
