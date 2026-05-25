from __future__ import annotations

from collections.abc import Sequence

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.reports import (
    ReportGroup,
    ReportResult,
    ReportRow,
    ReportSort,
    ReportSummary,
    ReportTimeframe,
    SavedReport,
)
from monarch_api.types.transactions import TransactionFilter


REPORT_SUMMARY_FIELDS = """
fragment ReportsSummaryFields on TransactionsSummary {
  sum
  avg
  count
  max
  sumIncome
  sumExpense
  savings
  savingsRate
  first
  last
}
"""

REPORT_DATA_QUERY = (
    """
query Common_GetReportsData(
  $filters: TransactionFilterInput!
  $groupBy: [ReportsGroupByEntity!]
  $groupByTimeframe: ReportsGroupByTimeframe
  $sortBy: ReportsSortBy
  $includeCategory: Boolean = false
  $includeCategoryGroup: Boolean = false
  $includeMerchant: Boolean = false
  $fillEmptyValues: Boolean = true
) {
  reports(
    groupBy: $groupBy
    groupByTimeframe: $groupByTimeframe
    filters: $filters
    sortBy: $sortBy
    fillEmptyValues: $fillEmptyValues
  ) {
    groupBy {
      date
      ...ReportsCategoryFields @include(if: $includeCategory)
      ...ReportsCategoryGroupFields @include(if: $includeCategoryGroup)
      ...ReportsMerchantFields @include(if: $includeMerchant)
    }
    summary {
      ...ReportsSummaryFields
    }
  }
  aggregates(filters: $filters, fillEmptyValues: $fillEmptyValues) {
    summary {
      ...ReportsSummaryFields
    }
  }
}

fragment ReportsCategoryFields on ReportsGroupByData {
  category {
    id
    name
    icon
    group {
      id
      name
      type
    }
  }
}

fragment ReportsCategoryGroupFields on ReportsGroupByData {
  categoryGroup {
    id
    name
    type
  }
}

fragment ReportsMerchantFields on ReportsGroupByData {
  merchant {
    id
    name
  }
}
"""
    + REPORT_SUMMARY_FIELDS
)

REPORT_CONFIGURATION_FIELDS = (
    """
fragment TransactionFilterSetFields on TransactionFilterSet {
  categories {
    id
    name
    icon
  }
  categoryGroups {
    id
    name
    type
  }
  accounts {
    id
    displayName
    logoUrl
    icon
  }
  merchants {
    id
    name
    logoUrl
  }
  tags {
    id
    name
    color
  }
  goals {
    id
    name
  }
  savingsGoals {
    id
    name
  }
  searchQuery
  categoryType
  isUncategorized
  startDate
  endDate
  absAmountGte
  absAmountLte
  isSplit
  isRecurring
  isPending
  creditsOnly
  debitsOnly
  hasNotes
  hasAttachments
  hiddenFromReports
  importedFromMint
  syncedFromInstitution
  needsReview
  needsReviewUnassigned
  needsReviewByUser {
    id
    name
  }
}

fragment ReportConfigurationFields on ReportConfiguration {
  id
  displayName
  transactionFilterSet {
    ...TransactionFilterSetFields
  }
  reportView {
    analysisScope
    chartType
    chartCalculation
    chartLayout
    chartDensity
    dimensions
    timeframe
  }
}
"""
)

LIST_SAVED_REPORTS_QUERY = (
    """
query Web_GetReportConfigurations {
  reportConfigurations {
    ...ReportConfigurationFields
  }
}
"""
    + REPORT_CONFIGURATION_FIELDS
)

CREATE_SAVED_REPORT_MUTATION = (
    """
mutation Web_CreateReportConfiguration($input: CreateReportConfigurationInput!) {
  createReportConfiguration(input: $input) {
    reportConfiguration {
      ...ReportConfigurationFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + REPORT_CONFIGURATION_FIELDS
)

UPDATE_SAVED_REPORT_MUTATION = (
    """
mutation Web_UpdateReportConfiguration($input: UpdateReportConfigurationInput!) {
  updateReportConfiguration(input: $input) {
    reportConfiguration {
      ...ReportConfigurationFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + REPORT_CONFIGURATION_FIELDS
)

DELETE_SAVED_REPORT_MUTATION = """
mutation Web_DeleteReportConfiguration($id: ID!) {
  deleteReportConfiguration(id: $id) {
    deleted
    errors {
      message
      code
    }
  }
}
"""


def get_report_data(
    session: AuthSession,
    *,
    filters: TransactionFilter | None = None,
    group_by: ReportGroup | Sequence[ReportGroup] | None = ReportGroup.CATEGORY,
    timeframe: ReportTimeframe | None = None,
    sort_by: ReportSort | None = None,
    fill_empty_values: bool = True,
) -> ReportResult:
    groups = _groups(group_by)
    data = graphql_request(
        session,
        "Common_GetReportsData",
        REPORT_DATA_QUERY,
        {
            "filters": filters.to_api() if filters is not None else {},
            "groupBy": [group.value for group in groups] or None,
            "groupByTimeframe": timeframe.value if timeframe is not None else None,
            "sortBy": sort_by.value if sort_by is not None else None,
            "includeCategory": ReportGroup.CATEGORY in groups,
            "includeCategoryGroup": ReportGroup.CATEGORY_GROUP in groups,
            "includeMerchant": ReportGroup.MERCHANT in groups,
            "fillEmptyValues": fill_empty_values,
        },
    )
    raw_rows = data.get("reports")
    rows = [
        ReportRow.from_api(row)
        for row in raw_rows
        if isinstance(row, dict)
    ] if isinstance(raw_rows, list) else []

    summary = ReportSummary.from_api(_summary(data.get("aggregates")))
    return ReportResult(summary=summary, rows=rows, raw=dict(data))


def list_saved_reports(session: AuthSession) -> list[SavedReport]:
    data = graphql_request(
        session,
        "Web_GetReportConfigurations",
        LIST_SAVED_REPORTS_QUERY,
    )
    raw_reports = data.get("reportConfigurations")
    if not isinstance(raw_reports, list):
        return []
    return [
        SavedReport.from_api(report)
        for report in raw_reports
        if isinstance(report, dict)
    ]


def get_saved_report(session: AuthSession, report_id: str) -> SavedReport | None:
    for report in list_saved_reports(session):
        if report.id == report_id:
            return report
    return None


def create_saved_report(
    session: AuthSession,
    name: str,
    *,
    filters: TransactionFilter | None = None,
    group_by: ReportGroup | Sequence[ReportGroup] | None = ReportGroup.CATEGORY,
    timeframe: ReportTimeframe | None = None,
) -> SavedReport:
    data = graphql_request(
        session,
        "Web_CreateReportConfiguration",
        CREATE_SAVED_REPORT_MUTATION,
        {
            "input": {
                "displayName": name,
                "transactionFilters": filters.to_api() if filters is not None else {},
                "reportView": _report_view(group_by, timeframe),
            }
        },
    )
    payload = _payload(data, "createReportConfiguration")
    _raise_payload_errors(payload)
    return _saved_report_payload(payload, "created")


def update_saved_report(
    session: AuthSession,
    report_id: str,
    *,
    name: str,
) -> SavedReport:
    data = graphql_request(
        session,
        "Web_UpdateReportConfiguration",
        UPDATE_SAVED_REPORT_MUTATION,
        {
            "input": {
                "id": report_id,
                "displayName": name,
            }
        },
    )
    payload = _payload(data, "updateReportConfiguration")
    _raise_payload_errors(payload)
    return _saved_report_payload(payload, "updated")


def delete_saved_report(session: AuthSession, report_id: str) -> bool:
    data = graphql_request(
        session,
        "Web_DeleteReportConfiguration",
        DELETE_SAVED_REPORT_MUTATION,
        {"id": report_id},
    )
    payload = _payload(data, "deleteReportConfiguration")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


def _groups(group_by: ReportGroup | Sequence[ReportGroup] | None) -> list[ReportGroup]:
    if group_by is None:
        return []
    if isinstance(group_by, ReportGroup):
        return [group_by]
    return list(group_by)


def _report_view(
    group_by: ReportGroup | Sequence[ReportGroup] | None,
    timeframe: ReportTimeframe | None,
) -> JsonDict:
    return _clean(
        {
            "dimensions": [group.value for group in _groups(group_by)] or None,
            "timeframe": timeframe.value if timeframe is not None else None,
        }
    )


def _summary(value: object) -> JsonDict:
    if not isinstance(value, list) or not value:
        return {}
    first = value[0]
    if not isinstance(first, dict):
        return {}
    summary = first.get("summary")
    return summary if isinstance(summary, dict) else {}


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


def _saved_report_payload(payload: JsonDict, action: str) -> SavedReport:
    report = payload.get("reportConfiguration")
    if not isinstance(report, dict):
        raise MonarchError(f"Monarch did not return the {action} saved report.")
    return SavedReport.from_api(report)


def _raise_payload_errors(payload: JsonDict) -> None:
    errors = payload.get("errors")
    if not errors:
        return
    if isinstance(errors, list):
        messages = []
        for error in errors:
            if isinstance(error, dict):
                messages.append(str(error.get("message") or error))
            elif error:
                messages.append(str(error))
        raise MonarchError("; ".join(messages) or "Monarch request failed.")
    if isinstance(errors, dict):
        raise MonarchError(str(errors.get("message") or errors))
    raise MonarchError(str(errors))


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}
