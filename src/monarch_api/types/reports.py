from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from monarch_api.types.categories import CategoryGroupReference, _category_type
from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    CategoryReference,
    MerchantReference,
    TransactionFilter,
    TransactionVisibility,
)


class ReportGroup(str, Enum):
    CATEGORY = "category"
    CATEGORY_GROUP = "category_group"
    MERCHANT = "merchant"


class ReportTimeframe(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ReportSort(str, Enum):
    TOTAL = "sum"
    INCOME = "sum_income"
    EXPENSES = "sum_expense"
    COUNT = "count"
    AVERAGE = "avg"
    MAX = "max"


@dataclass(slots=True)
class ReportSummary:
    total: float | None = None
    average: float | None = None
    count: int | None = None
    max: float | None = None
    income: float | None = None
    expenses: float | None = None
    savings: float | None = None
    savings_rate: float | None = None
    first_date: str | None = None
    last_date: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReportSummary:
        data = data or {}
        return cls(
            total=_float(data.get("sum")),
            average=_float(data.get("avg")),
            count=_int(data.get("count")),
            max=_float(data.get("max")),
            income=_float(data.get("sumIncome")),
            expenses=_float(data.get("sumExpense")),
            savings=_float(data.get("savings")),
            savings_rate=_float(data.get("savingsRate")),
            first_date=data.get("first"),
            last_date=data.get("last"),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReportGroupValue:
    date: str | None = None
    category: CategoryReference | None = None
    category_group: CategoryGroupReference | None = None
    merchant: MerchantReference | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReportGroupValue:
        data = data or {}
        return cls(
            date=data.get("date"),
            category=CategoryReference.from_api(data.get("category")),
            category_group=CategoryGroupReference.from_api(data.get("categoryGroup")),
            merchant=MerchantReference.from_api(data.get("merchant")),
            raw=dict(data),
        )

    @property
    def label(self) -> str:
        if self.category is not None:
            return self.category.name
        if self.category_group is not None:
            return self.category_group.name or self.category_group.id
        if self.merchant is not None:
            return self.merchant.name
        return self.date or ""


@dataclass(slots=True)
class ReportRow:
    group: ReportGroupValue
    summary: ReportSummary
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> ReportRow:
        return cls(
            group=ReportGroupValue.from_api(_dict(data.get("groupBy"))),
            summary=ReportSummary.from_api(_dict(data.get("summary"))),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReportResult:
    summary: ReportSummary
    rows: list[ReportRow]
    raw: JsonDict | None = None


@dataclass(slots=True)
class SavedReport:
    id: str
    name: str
    filters: TransactionFilter | None = None
    group_by: list[ReportGroup] | None = None
    timeframe: ReportTimeframe | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> SavedReport:
        report_view = _dict(data.get("reportView"))
        dimensions = report_view.get("dimensions")
        groups = _report_groups(dimensions)
        return cls(
            id=str(data["id"]),
            name=str(data.get("displayName") or ""),
            filters=_filter_from_api(_dict(data.get("transactionFilterSet"))),
            group_by=groups,
            timeframe=_report_timeframe(report_view.get("timeframe")),
            raw=dict(data),
        )


def _filter_from_api(data: JsonDict) -> TransactionFilter | None:
    if not data:
        return None
    return TransactionFilter(
        start_date=data.get("startDate"),
        end_date=data.get("endDate"),
        search=data.get("searchQuery"),
        account_ids=_ids(data.get("accounts")),
        category_ids=_ids(data.get("categories")),
        category_group_ids=_ids(data.get("categoryGroups")),
        merchant_ids=_ids(data.get("merchants")),
        tag_ids=_ids(data.get("tags")),
        goal_ids=_ids(data.get("goals")) or _ids(data.get("savingsGoals")),
        min_absolute_amount=_float(data.get("absAmountGte")),
        max_absolute_amount=_float(data.get("absAmountLte")),
        category_type=_category_type(data.get("categoryType")),
        credits_only=data.get("creditsOnly"),
        debits_only=data.get("debitsOnly"),
        is_pending=data.get("isPending"),
        is_recurring=data.get("isRecurring"),
        is_split=data.get("isSplit"),
        is_uncategorized=data.get("isUncategorized"),
        is_untagged=data.get("isUntagged"),
        has_notes=data.get("hasNotes"),
        has_attachments=data.get("hasAttachments"),
        hide_from_reports=data.get("hiddenFromReports"),
        needs_review=data.get("needsReview"),
        needs_review_by_user_id=_nested_id(data.get("needsReviewByUser")),
        needs_review_unassigned=data.get("needsReviewUnassigned"),
        synced_from_institution=data.get("syncedFromInstitution"),
        imported_from_mint=data.get("importedFromMint"),
        transaction_visibility=_transaction_visibility(data.get("transactionVisibility")),
    )


def _report_group(value: object) -> ReportGroup | None:
    if value is None:
        return None
    try:
        return ReportGroup(str(value))
    except ValueError:
        return None


def _report_groups(value: object) -> list[ReportGroup] | None:
    if not isinstance(value, list):
        return None
    groups: list[ReportGroup] = []
    for item in value:
        group = _report_group(item)
        if group is not None:
            groups.append(group)
    return groups


def _report_timeframe(value: object) -> ReportTimeframe | None:
    if value is None:
        return None
    try:
        return ReportTimeframe(str(value))
    except ValueError:
        return None


def _transaction_visibility(value: object) -> TransactionVisibility | None:
    if value is None:
        return None
    try:
        return TransactionVisibility(str(value))
    except ValueError:
        return None


def _ids(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    ids = [_nested_id(item) for item in value]
    return [id_ for id_ in ids if id_ is not None]


def _nested_id(data: object) -> str | None:
    if not isinstance(data, dict) or data.get("id") is None:
        return None
    return str(data["id"])


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
