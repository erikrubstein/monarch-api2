from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    AccountReference,
    CategoryReference,
    MerchantReference,
)


class RecurringFrequency(str, Enum):
    WEEKLY = "weekly"
    EVERY_TWO_WEEKS = "every_two_weeks"
    TWICE_A_MONTH = "twice_a_month"
    MONTHLY = "monthly"
    EVERY_TWO_MONTHS = "every_two_months"
    QUARTERLY = "quarterly"
    EVERY_SIX_MONTHS = "every_six_months"
    YEARLY = "yearly"


class RecurringType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    CREDIT_CARD = "credit_card"


class RecurringStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    IGNORED = "ignored"


@dataclass(slots=True)
class RecurringFilter:
    account_ids: list[str] | None = None
    category_ids: list[str] | None = None
    merchant_ids: list[str] | None = None
    recurring_ids: list[str] | None = None
    frequencies: list[RecurringFrequency | str] | None = None
    recurring_types: list[RecurringType | str] | None = None
    is_completed: bool | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "accounts": self.account_ids,
                "categories": self.category_ids,
                "merchantIds": self.merchant_ids,
                "ids": self.recurring_ids,
                "frequencies": _values(self.frequencies),
                "recurringTypes": _values(self.recurring_types),
                "isCompleted": self.is_completed,
            }
        )


@dataclass(slots=True)
class RecurringStream:
    id: str
    name: str
    frequency: str | None = None
    amount: float | None = None
    next_date: str | None = None
    next_amount: float | None = None
    base_date: str | None = None
    day_of_month: int | None = None
    is_active: bool | None = None
    is_approximate: bool | None = None
    recurring_type: RecurringType | None = None
    status: RecurringStatus | None = None
    merchant: MerchantReference | None = None
    account: AccountReference | None = None
    category: CategoryReference | None = None
    liability_account_id: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> RecurringStream:
        stream = _dict(data.get("stream")) or data
        next_transaction = _dict(data.get("nextForecastedTransaction"))
        return cls(
            id=str(stream["id"]),
            name=str(stream.get("name") or ""),
            frequency=stream.get("frequency"),
            amount=_float(stream.get("amount")),
            next_date=next_transaction.get("date"),
            next_amount=_float(next_transaction.get("amount")),
            base_date=stream.get("baseDate"),
            day_of_month=_int(stream.get("dayOfTheMonth")),
            is_active=stream.get("isActive"),
            is_approximate=stream.get("isApproximate"),
            recurring_type=_recurring_type(stream.get("recurringType")),
            status=_status(stream),
            merchant=MerchantReference.from_api(stream.get("merchant")),
            account=AccountReference.from_api(data.get("account")),
            category=CategoryReference.from_api(data.get("category")),
            liability_account_id=_liability_account_id(stream),
            raw=dict(data),
        )


@dataclass(slots=True)
class RecurringOccurrence:
    recurring_id: str
    date: str
    amount: float | None = None
    name: str = ""
    frequency: str | None = None
    merchant: MerchantReference | None = None
    account: AccountReference | None = None
    category: CategoryReference | None = None
    transaction_id: str | None = None
    is_past: bool | None = None
    is_late: bool | None = None
    is_completed: bool | None = None
    marked_paid_at: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> RecurringOccurrence:
        stream = _dict(data.get("stream"))
        return cls(
            recurring_id=str(stream["id"]),
            date=str(data.get("date") or ""),
            amount=_float(data.get("amount")),
            name=str(stream.get("name") or ""),
            frequency=stream.get("frequency"),
            merchant=MerchantReference.from_api(stream.get("merchant")),
            account=AccountReference.from_api(data.get("account")),
            category=CategoryReference.from_api(data.get("category")),
            transaction_id=data.get("transactionId"),
            is_past=data.get("isPast"),
            is_late=data.get("isLate"),
            is_completed=data.get("isCompleted"),
            marked_paid_at=data.get("markedPaidAt"),
            raw=dict(data),
        )


@dataclass(slots=True)
class RecurringSummaryBucket:
    completed: float | None = None
    remaining: float | None = None
    total: float | None = None
    count: int | None = None
    pending_amount_count: int | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> RecurringSummaryBucket:
        data = data or {}
        return cls(
            completed=_float(data.get("completed")),
            remaining=_float(data.get("remaining")),
            total=_float(data.get("total")),
            count=_int(data.get("count")),
            pending_amount_count=_int(data.get("pendingAmountCount")),
            raw=dict(data),
        )


@dataclass(slots=True)
class RecurringSummary:
    expense: RecurringSummaryBucket
    income: RecurringSummaryBucket
    credit_card: RecurringSummaryBucket
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> RecurringSummary:
        data = data or {}
        return cls(
            expense=RecurringSummaryBucket.from_api(_dict(data.get("expense"))),
            income=RecurringSummaryBucket.from_api(_dict(data.get("income"))),
            credit_card=RecurringSummaryBucket.from_api(_dict(data.get("creditCard"))),
            raw=dict(data),
        )


def _status(data: JsonDict) -> RecurringStatus | None:
    review_status = data.get("reviewStatus")
    if review_status == "ignored":
        return RecurringStatus.IGNORED
    if review_status == "pending":
        return RecurringStatus.PENDING
    if data.get("isActive") is True:
        return RecurringStatus.ACTIVE
    if data.get("isActive") is False:
        return RecurringStatus.INACTIVE
    return None


def _recurring_type(value: object) -> RecurringType | None:
    if value is None:
        return None
    try:
        return RecurringType(str(value))
    except ValueError:
        return None


def _liability_account_id(data: JsonDict) -> str | None:
    liability = _dict(data.get("creditReportLiabilityAccount"))
    account = _dict(liability.get("account"))
    if account.get("id") is not None:
        return str(account["id"])
    return None


def _values(values: Sequence[Enum | str] | None) -> list[str] | None:
    if values is None:
        return None
    return [value.value if isinstance(value, Enum) else str(value) for value in values]


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _dict(value: object) -> JsonDict:
    if isinstance(value, dict):
        return value
    return {}


def _float(value: object) -> float | None:
    if not isinstance(value, int | float | str) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(value: object) -> int | None:
    if not isinstance(value, int | float | str) or isinstance(value, bool):
        return None
    try:
        return int(value)
    except ValueError:
        return None
