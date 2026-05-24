from __future__ import annotations

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.cashflow import (
    CashflowBreakdown,
    CashflowBreakdownDirection,
    CashflowBreakdownGroup,
    CashflowBreakdownRow,
    CashflowFilter,
    CashflowInterval,
    CashflowSummary,
    CashflowTrendPoint,
)
from monarch_api.types.categories import CategoryGroupReference, CategoryType
from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    CategoryReference,
    MerchantReference,
    TransactionVisibility,
)


CASHFLOW_TIMEFRAME_QUERY = """
query Common_GetCashFlowTimeframeAggregates($filters: TransactionFilterInput) {
  byYear: aggregates(groupBy: ["year"], fillEmptyValues: true, filters: $filters) {
    groupBy {
      year
    }
    summary {
      savings
      savingsRate
      sumIncome
      sumExpense
    }
  }
  byMonth: aggregates(groupBy: ["month"], fillEmptyValues: true, filters: $filters) {
    groupBy {
      month
    }
    summary {
      savings
      savingsRate
      sumIncome
      sumExpense
    }
  }
  byQuarter: aggregates(groupBy: ["quarter"], fillEmptyValues: true, filters: $filters) {
    groupBy {
      quarter
    }
    summary {
      savings
      savingsRate
      sumIncome
      sumExpense
    }
  }
}
"""

CASHFLOW_ENTITY_QUERY = """
query Common_GetCashFlowEntityAggregates($filters: TransactionFilterInput) {
  byCategory: aggregates(filters: $filters, groupBy: ["category"]) {
    groupBy {
      category {
        id
        name
        icon
        group {
          id
          type
        }
      }
    }
    summary {
      sum
      count
    }
  }
  byCategoryGroup: aggregates(filters: $filters, groupBy: ["categoryGroup"]) {
    groupBy {
      categoryGroup {
        id
        name
        type
      }
    }
    summary {
      sum
      count
    }
  }
  byMerchant: aggregates(filters: $filters, groupBy: ["merchant"]) {
    groupBy {
      merchant {
        id
        name
        logoUrl
      }
    }
    summary {
      sumIncome
      sumExpense
      count
    }
  }
  summary: aggregates(filters: $filters, fillEmptyValues: true) {
    summary {
      sumIncome
      sumExpense
      savings
      savingsRate
    }
  }
}
"""


def get_cashflow_summary(
    session: AuthSession,
    start_date: str,
    end_date: str,
    *,
    filters: CashflowFilter | None = None,
) -> CashflowSummary:
    data = graphql_request(
        session,
        "Common_GetCashFlowEntityAggregates",
        CASHFLOW_ENTITY_QUERY,
        {"filters": _filters(start_date, end_date, filters)},
    )
    summary = _summary(data)
    return CashflowSummary.from_api(
        summary,
        start_date=start_date,
        end_date=end_date,
    )


def get_cashflow_trends(
    session: AuthSession,
    start_date: str,
    end_date: str,
    *,
    interval: CashflowInterval = CashflowInterval.MONTH,
    filters: CashflowFilter | None = None,
) -> list[CashflowTrendPoint]:
    data = graphql_request(
        session,
        "Common_GetCashFlowTimeframeAggregates",
        CASHFLOW_TIMEFRAME_QUERY,
        {"filters": _filters(start_date, end_date, filters)},
    )
    raw_points = data.get(_trend_key(interval))
    if not isinstance(raw_points, list):
        return []
    points = [
        CashflowTrendPoint.from_api(point, interval=interval)
        for point in raw_points
        if isinstance(point, dict)
    ]
    return sorted(points, key=lambda point: point.start_date)


def get_cashflow_breakdown(
    session: AuthSession,
    start_date: str,
    end_date: str,
    direction: CashflowBreakdownDirection,
    *,
    group_by: CashflowBreakdownGroup = CashflowBreakdownGroup.CATEGORY,
    filters: CashflowFilter | None = None,
) -> CashflowBreakdown:
    data = graphql_request(
        session,
        "Common_GetCashFlowEntityAggregates",
        CASHFLOW_ENTITY_QUERY,
        {
            "filters": _filters(
                start_date,
                end_date,
                filters,
                category_type=_category_type_for_direction(direction),
            )
        },
    )
    rows = _breakdown_rows(data, direction, group_by)
    return CashflowBreakdown(
        direction=direction,
        group_by=group_by,
        rows=rows,
    )


def _breakdown_rows(
    data: JsonDict,
    direction: CashflowBreakdownDirection,
    group_by: CashflowBreakdownGroup,
) -> list[CashflowBreakdownRow]:
    if group_by is CashflowBreakdownGroup.CATEGORY:
        rows = _category_rows(data.get("byCategory"), direction)
    elif group_by is CashflowBreakdownGroup.CATEGORY_GROUP:
        rows = _category_group_rows(data.get("byCategoryGroup"), direction)
    elif group_by is CashflowBreakdownGroup.MERCHANT:
        rows = _merchant_rows(data.get("byMerchant"), direction)
    else:
        raise MonarchError(f"Unsupported cashflow breakdown group: {group_by}")

    total = sum(row.amount for row in rows)
    if total != 0:
        rows = [
            _with_percent(row, round((row.amount / total) * 100, 2))
            for row in rows
        ]
    return sorted(rows, key=lambda row: (-row.amount, row.name.casefold(), row.id or ""))


def _category_rows(
    data: object,
    direction: CashflowBreakdownDirection,
) -> list[CashflowBreakdownRow]:
    rows = []
    for item in _list(data):
        group_by = _dict(item.get("groupBy"))
        category = _dict(group_by.get("category"))
        if not category:
            continue
        reference = CategoryReference.from_api(category)
        amount = _directed_amount(_summary_dict(item).get("sum"), direction)
        if amount == 0:
            continue
        rows.append(
            CashflowBreakdownRow(
                id=reference.id,
                name=reference.name,
                amount=amount,
                transaction_count=_count(_summary_dict(item).get("count")),
                category=reference,
                raw=dict(item),
            )
        )
    return rows


def _category_group_rows(
    data: object,
    direction: CashflowBreakdownDirection,
) -> list[CashflowBreakdownRow]:
    rows = []
    for item in _list(data):
        group_by = _dict(item.get("groupBy"))
        category_group = _dict(group_by.get("categoryGroup"))
        if not category_group:
            continue
        reference = CategoryGroupReference.from_api(category_group)
        amount = _directed_amount(_summary_dict(item).get("sum"), direction)
        if amount == 0:
            continue
        rows.append(
            CashflowBreakdownRow(
                id=reference.id,
                name=reference.name or "",
                amount=amount,
                transaction_count=_count(_summary_dict(item).get("count")),
                category_group=reference,
                raw=dict(item),
            )
        )
    return rows


def _merchant_rows(
    data: object,
    direction: CashflowBreakdownDirection,
) -> list[CashflowBreakdownRow]:
    rows = []
    key = "sumIncome" if direction is CashflowBreakdownDirection.INCOME else "sumExpense"
    for item in _list(data):
        group_by = _dict(item.get("groupBy"))
        merchant = _dict(group_by.get("merchant"))
        if not merchant:
            continue
        reference = MerchantReference.from_api(merchant)
        amount = _directed_amount(_summary_dict(item).get(key), direction)
        if amount == 0:
            continue
        rows.append(
            CashflowBreakdownRow(
                id=reference.id,
                name=reference.name,
                amount=amount,
                transaction_count=_count(_summary_dict(item).get("count")),
                merchant=reference,
                raw=dict(item),
            )
        )
    return rows


def _category_type_for_direction(direction: CashflowBreakdownDirection) -> CategoryType:
    if direction is CashflowBreakdownDirection.INCOME:
        return CategoryType.INCOME
    return CategoryType.EXPENSE


def _directed_amount(
    value: object,
    direction: CashflowBreakdownDirection,
) -> float:
    amount = _amount(value)
    if direction is CashflowBreakdownDirection.EXPENSES:
        return -amount
    return amount


def _filters(
    start_date: str,
    end_date: str,
    filters: CashflowFilter | None,
    *,
    category_type: CategoryType | None = None,
) -> JsonDict:
    filters = filters or CashflowFilter()
    return _clean(
        {
            "startDate": start_date,
            "endDate": end_date,
            "accounts": filters.account_ids,
            "categories": filters.category_ids,
            "categoryGroups": filters.category_group_ids,
            "merchants": filters.merchant_ids,
            "tags": filters.tag_ids,
            "categoryType": category_type.value if category_type is not None else None,
            "transactionVisibility": (
                TransactionVisibility.ALL.value
                if filters.include_hidden
                else TransactionVisibility.VISIBLE_ONLY.value
            ),
        }
    )


def _summary(data: JsonDict) -> JsonDict:
    summary_aggregates = data.get("summary")
    first = _first(summary_aggregates)
    return _summary_dict(first)


def _summary_dict(data: JsonDict) -> JsonDict:
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return {}
    return summary


def _trend_key(interval: CashflowInterval) -> str:
    if interval is CashflowInterval.YEAR:
        return "byYear"
    if interval is CashflowInterval.QUARTER:
        return "byQuarter"
    return "byMonth"


def _with_percent(
    row: CashflowBreakdownRow,
    percent: float,
) -> CashflowBreakdownRow:
    row.percent = percent
    return row


def _amount(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _count(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _dict(value: object) -> JsonDict:
    if not isinstance(value, dict):
        return {}
    return value


def _first(data: object) -> JsonDict:
    values = _list(data)
    if not values:
        return {}
    return values[0]


def _list(data: object) -> list[JsonDict]:
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]
