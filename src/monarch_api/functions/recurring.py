from __future__ import annotations

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.recurring import (
    RecurringFilter,
    RecurringFrequency,
    RecurringOccurrence,
    RecurringStream,
    RecurringSummary,
)


RECURRING_STREAM_FIELDS = """
fragment RecurringStreamFields on RecurringTransactionStream {
  id
  reviewStatus
  frequency
  amount
  baseDate
  dayOfTheMonth
  isActive
  isApproximate
  name
  logoUrl
  recurringType
  merchant {
    id
    name
    logoUrl
  }
  creditReportLiabilityAccount {
    id
    account {
      id
    }
  }
}
"""

RECURRING_OCCURRENCE_FIELDS = (
    """
fragment RecurringOccurrenceFields on RecurringTransactionCalendarItem {
  stream {
    ...RecurringStreamFields
  }
  date
  isPast
  isLate
  markedPaidAt
  isCompleted
  transactionId
  amount
  category {
    id
    name
    icon
  }
  account {
    id
    displayName
    icon
    logoUrl
  }
}
"""
    + RECURRING_STREAM_FIELDS
)

LIST_RECURRING_STREAMS_QUERY = (
    """
query Common_GetAllRecurringTransactionItems(
  $filters: RecurringTransactionFilter
  $includeLiabilities: Boolean
  $includePending: Boolean
) {
  recurringTransactionStreams(
    filters: $filters
    includeLiabilities: $includeLiabilities
    includePending: $includePending
  ) {
    stream {
      ...RecurringStreamFields
    }
    nextForecastedTransaction {
      date
      amount
    }
    category {
      id
      name
      icon
    }
    account {
      id
      displayName
      icon
      logoUrl
    }
  }
}
"""
    + RECURRING_STREAM_FIELDS
)

LIST_STREAM_SETTINGS_QUERY = (
    """
query Common_GetRecurringStreams($includeLiabilities: Boolean) {
  recurringTransactionStreams(
    includePending: true
    includeLiabilities: $includeLiabilities
  ) {
    stream {
      ...RecurringStreamFields
    }
  }
}
"""
    + RECURRING_STREAM_FIELDS
)

LIST_RECURRING_OCCURRENCES_QUERY = (
    """
query Web_GetDashboardUpcomingRecurringTransactionItems(
  $startDate: Date!
  $endDate: Date!
  $includeLiabilities: Boolean
  $filters: RecurringTransactionFilter
) {
  recurringTransactionItems(
    startDate: $startDate
    endDate: $endDate
    includeLiabilities: $includeLiabilities
    filters: $filters
  ) {
    ...RecurringOccurrenceFields
  }
}
"""
    + RECURRING_OCCURRENCE_FIELDS
)

RECURRING_SUMMARY_QUERY = (
    """
query Common_GetAggregatedRecurringItems(
  $startDate: Date!
  $endDate: Date!
  $filters: RecurringTransactionFilter
) {
  aggregatedRecurringItems(
    startDate: $startDate
    endDate: $endDate
    groupBy: "status"
    filters: $filters
  ) {
    aggregatedSummary {
      expense {
        completed
        remaining
        total
        count
        pendingAmountCount
      }
      creditCard {
        completed
        remaining
        total
        count
        pendingAmountCount
      }
      income {
        completed
        remaining
        total
      }
    }
  }
}
"""
)

UPDATE_RECURRING_STREAM_MUTATION = """
mutation Common_RecurringUpdateMerchant($input: UpdateMerchantInput!) {
  updateMerchant(input: $input) {
    merchant {
      id
    }
    errors {
      message
      code
    }
  }
}
"""

MARK_NOT_RECURRING_MUTATION = """
mutation Common_MarkAsNotRecurring($streamId: ID!) {
  markStreamAsNotRecurring(streamId: $streamId) {
    success
    errors {
      message
      code
    }
  }
}
"""


def list_recurring_streams(
    session: AuthSession,
    *,
    filters: RecurringFilter | None = None,
    include_pending: bool = True,
    include_liabilities: bool = True,
) -> list[RecurringStream]:
    data = graphql_request(
        session,
        "Common_GetAllRecurringTransactionItems",
        LIST_RECURRING_STREAMS_QUERY,
        {
            "filters": filters.to_api() if filters is not None else {},
            "includePending": include_pending,
            "includeLiabilities": include_liabilities,
        },
    )
    raw_streams = data.get("recurringTransactionStreams")
    if not isinstance(raw_streams, list):
        return []
    return [
        RecurringStream.from_api(stream)
        for stream in raw_streams
        if isinstance(stream, dict)
    ]


def get_recurring_stream(
    session: AuthSession,
    recurring_id: str,
    *,
    include_liabilities: bool = True,
) -> RecurringStream | None:
    filters = RecurringFilter(recurring_ids=[recurring_id])
    streams = list_recurring_streams(
        session,
        filters=filters,
        include_liabilities=include_liabilities,
    )
    if streams:
        return streams[0]

    for stream in _list_stream_settings(session, include_liabilities=include_liabilities):
        if stream.id == recurring_id:
            return stream
    return None


def list_recurring_occurrences(
    session: AuthSession,
    start_date: str,
    end_date: str,
    *,
    filters: RecurringFilter | None = None,
    include_liabilities: bool = True,
) -> list[RecurringOccurrence]:
    data = graphql_request(
        session,
        "Web_GetDashboardUpcomingRecurringTransactionItems",
        LIST_RECURRING_OCCURRENCES_QUERY,
        {
            "startDate": start_date,
            "endDate": end_date,
            "filters": filters.to_api() if filters is not None else {},
            "includeLiabilities": include_liabilities,
        },
    )
    raw_items = data.get("recurringTransactionItems")
    if not isinstance(raw_items, list):
        return []
    return [
        RecurringOccurrence.from_api(item)
        for item in raw_items
        if isinstance(item, dict)
    ]


def get_recurring_summary(
    session: AuthSession,
    start_date: str,
    end_date: str,
    *,
    filters: RecurringFilter | None = None,
) -> RecurringSummary:
    data = graphql_request(
        session,
        "Common_GetAggregatedRecurringItems",
        RECURRING_SUMMARY_QUERY,
        {
            "startDate": start_date,
            "endDate": end_date,
            "filters": filters.to_api() if filters is not None else {},
        },
    )
    recurring = _dict(data.get("aggregatedRecurringItems"))
    return RecurringSummary.from_api(_dict(recurring.get("aggregatedSummary")))


def create_recurring_stream(
    session: AuthSession,
    merchant_id: str,
    *,
    frequency: RecurringFrequency | str,
    amount: float,
    base_date: str,
    is_active: bool = True,
) -> RecurringStream:
    recurrence = _recurrence_payload(
        frequency=frequency,
        amount=amount,
        base_date=base_date,
        is_active=is_active,
    )
    _update_merchant_recurrence(session, merchant_id, recurrence)

    created = _get_stream_for_merchant(session, merchant_id)
    if created is None:
        raise MonarchError("Monarch did not return the created recurring stream.")
    return created


def update_recurring_stream(
    session: AuthSession,
    recurring_id: str,
    *,
    frequency: str | None = None,
    amount: float | None = None,
    base_date: str | None = None,
    is_active: bool | None = None,
) -> RecurringStream:
    current = get_recurring_stream(session, recurring_id)
    if current is None:
        raise MonarchError("Recurring stream not found.")
    if current.merchant is None:
        raise MonarchError("Only merchant-backed recurring streams can be updated.")

    recurrence = _recurrence_payload(
        frequency=frequency if frequency is not None else current.frequency,
        amount=amount if amount is not None else current.amount,
        base_date=base_date if base_date is not None else current.base_date,
        is_active=is_active if is_active is not None else current.is_active,
    )
    _update_merchant_recurrence(session, current.merchant.id, recurrence)

    updated = get_recurring_stream(session, recurring_id)
    if updated is None:
        raise MonarchError("Monarch did not return the updated recurring stream.")
    return updated


def remove_recurring_stream(session: AuthSession, recurring_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_MarkAsNotRecurring",
        MARK_NOT_RECURRING_MUTATION,
        {"streamId": recurring_id},
    )
    payload = _payload(data, "markStreamAsNotRecurring")
    _raise_payload_errors(payload)
    return bool(payload.get("success"))


def _update_merchant_recurrence(
    session: AuthSession,
    merchant_id: str,
    recurrence: JsonDict,
) -> None:
    data = graphql_request(
        session,
        "Common_RecurringUpdateMerchant",
        UPDATE_RECURRING_STREAM_MUTATION,
        {
            "input": {
                "merchantId": merchant_id,
                "recurrence": recurrence,
            }
        },
    )
    payload = _payload(data, "updateMerchant")
    _raise_payload_errors(payload)


def _get_stream_for_merchant(
    session: AuthSession,
    merchant_id: str,
) -> RecurringStream | None:
    filters = RecurringFilter(merchant_ids=[merchant_id])
    streams = list_recurring_streams(session, filters=filters)
    if not streams:
        streams = _list_stream_settings(session, include_liabilities=True)

    for stream in streams:
        if stream.merchant is not None and stream.merchant.id == merchant_id:
            return stream
    return None


def _list_stream_settings(
    session: AuthSession,
    *,
    include_liabilities: bool,
) -> list[RecurringStream]:
    data = graphql_request(
        session,
        "Common_GetRecurringStreams",
        LIST_STREAM_SETTINGS_QUERY,
        {"includeLiabilities": include_liabilities},
    )
    raw_streams = data.get("recurringTransactionStreams")
    if not isinstance(raw_streams, list):
        return []
    return [
        RecurringStream.from_api(stream)
        for stream in raw_streams
        if isinstance(stream, dict)
    ]


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


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


def _recurrence_payload(
    *,
    frequency: RecurringFrequency | str | None,
    amount: float | None,
    base_date: str | None,
    is_active: bool | None,
) -> JsonDict:
    return _clean(
        {
            "isRecurring": True,
            "frequency": (
                frequency.value if isinstance(frequency, RecurringFrequency) else frequency
            ),
            "amount": amount,
            "baseDate": base_date,
            "isActive": is_active,
        }
    )


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _dict(value: object) -> JsonDict:
    if isinstance(value, dict):
        return value
    return {}
