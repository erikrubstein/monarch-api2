from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from monarch_api.types.common import JsonDict


class MerchantSort(str, Enum):
    NAME = "NAME"
    TRANSACTION_COUNT = "TRANSACTION_COUNT"


@dataclass(slots=True)
class Merchant:
    id: str
    name: str
    logo_url: str | None = None
    transaction_count: int | None = None
    rule_count: int | None = None
    can_be_deleted: bool | None = None
    recurring_id: str | None = None
    created_at: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Merchant:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            logo_url=data.get("logoUrl"),
            transaction_count=data.get("transactionCount"),
            rule_count=data.get("ruleCount"),
            can_be_deleted=data.get("canBeDeleted"),
            recurring_id=_recurring_id(data.get("recurringTransactionStream")),
            created_at=data.get("createdAt"),
            raw=dict(data),
        )


def _recurring_id(data: object) -> str | None:
    if not isinstance(data, dict) or data.get("id") is None:
        return None
    return str(data["id"])
