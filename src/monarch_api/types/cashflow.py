from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from enum import Enum

from monarch_api.types.categories import CategoryGroupReference
from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import CategoryReference, MerchantReference


class CashflowInterval(str, Enum):
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class CashflowBreakdownDirection(str, Enum):
    INCOME = "income"
    EXPENSES = "expenses"


class CashflowBreakdownGroup(str, Enum):
    CATEGORY = "category"
    CATEGORY_GROUP = "category_group"
    MERCHANT = "merchant"


@dataclass(slots=True)
class CashflowFilter:
    account_ids: list[str] | None = None
    category_ids: list[str] | None = None
    category_group_ids: list[str] | None = None
    merchant_ids: list[str] | None = None
    tag_ids: list[str] | None = None
    include_hidden: bool = False


@dataclass(slots=True)
class CashflowSummary:
    start_date: str
    end_date: str
    income: float
    expenses: float
    savings: float
    savings_rate: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        start_date: str,
        end_date: str,
    ) -> CashflowSummary:
        return cls(
            start_date=start_date,
            end_date=end_date,
            income=_amount(data.get("sumIncome")),
            expenses=abs(_amount(data.get("sumExpense"))),
            savings=_amount(data.get("savings")),
            savings_rate=_optional_float(data.get("savingsRate")),
            raw=dict(data),
        )


@dataclass(slots=True)
class CashflowTrendPoint:
    start_date: str
    end_date: str
    label: str | None
    income: float
    expenses: float
    savings: float
    savings_rate: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        interval: CashflowInterval,
    ) -> CashflowTrendPoint:
        group_by = data.get("groupBy")
        period = _period_label(group_by, interval)
        start_date, end_date = _period_bounds(period, interval)
        summary = _summary(data)
        return cls(
            start_date=start_date,
            end_date=end_date,
            label=period,
            income=_amount(summary.get("sumIncome")),
            expenses=abs(_amount(summary.get("sumExpense"))),
            savings=_amount(summary.get("savings")),
            savings_rate=_optional_float(summary.get("savingsRate")),
            raw=dict(data),
        )


@dataclass(slots=True)
class CashflowBreakdownRow:
    id: str | None
    name: str
    amount: float
    percent: float | None = None
    transaction_count: int | None = None
    category: CategoryReference | None = None
    category_group: CategoryGroupReference | None = None
    merchant: MerchantReference | None = None
    raw: JsonDict | None = None


@dataclass(slots=True)
class CashflowBreakdown:
    direction: CashflowBreakdownDirection
    group_by: CashflowBreakdownGroup
    rows: list[CashflowBreakdownRow]


def _amount(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _period_label(data: object, interval: CashflowInterval) -> str | None:
    if not isinstance(data, dict):
        return None
    value = data.get(interval.value)
    if value is None:
        return None
    return str(value)


def _period_bounds(
    period: str | None,
    interval: CashflowInterval,
) -> tuple[str, str]:
    if period is None:
        return "", ""
    try:
        start = date.fromisoformat(period)
    except ValueError:
        return period, period
    if interval is CashflowInterval.YEAR:
        return date(start.year, 1, 1).isoformat(), date(start.year, 12, 31).isoformat()
    if interval is CashflowInterval.QUARTER:
        end_month = start.month + 2
        return start.isoformat(), date(
            start.year,
            end_month,
            monthrange(start.year, end_month)[1],
        ).isoformat()
    return start.isoformat(), date(
        start.year,
        start.month,
        monthrange(start.year, start.month)[1],
    ).isoformat()


def _summary(data: JsonDict) -> JsonDict:
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return {}
    return summary
