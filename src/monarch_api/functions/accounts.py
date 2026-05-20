from __future__ import annotations

from datetime import date

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.accounts import (
    Account,
    AccountBalance,
    AccountFilter,
    AccountHistoryPoint,
    NetWorthBreakdownPoint,
    NetWorthSnapshot,
)
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict


ACCOUNT_FIELDS = """
fragment AccountFields on Account {
  id
  displayName
  displayBalance
  currentBalance
  displayLastUpdatedAt
  syncDisabled
  isHidden
  isAsset
  includeInNetWorth
  isManual
  icon
  logoUrl
  type {
    name
    display
    group
  }
  subtype {
    name
    display
  }
  institution {
    id
    name
    logo
    primaryColor
  }
  ownedByUser {
    id
    displayName
    profilePictureUrl
  }
}
"""

LIST_ACCOUNTS_QUERY = (
    """
query Common_GetAccounts($filters: AccountFilters) {
  accounts(filters: $filters) {
    ...AccountFields
  }
}
"""
    + ACCOUNT_FIELDS
)

GET_ACCOUNT_QUERY = (
    """
query Common_GetAccount($id: UUID!) {
  account(id: $id) {
    ...AccountFields
  }
}
"""
    + ACCOUNT_FIELDS
)

GET_NET_WORTH_PERFORMANCE_QUERY = """
query Common_GetAggregateSnapshots($filters: AggregateSnapshotFilters) {
  aggregateSnapshots(filters: $filters) {
    date
    balance
    assetsBalance
    liabilitiesBalance
  }
}
"""

GET_NET_WORTH_BREAKDOWN_QUERY = """
query Common_GetSnapshotsByAccountType(
  $startDate: Date!
  $timeframe: Timeframe!
  $filters: AccountFilters
) {
  snapshotsByAccountType(
    startDate: $startDate
    timeframe: $timeframe
    filters: $filters
  ) {
    accountType
    month
    balance
  }
  accountTypes {
    name
    group
  }
}
"""

GET_HISTORICAL_BALANCE_QUERY = """
query Common_GetDisplayBalanceAtDate($date: Date!, $filters: AccountFilters) {
  accounts(filters: $filters) {
    id
    displayBalance(date: $date)
    includeInNetWorth
    type {
      name
    }
  }
}
"""

GET_ACCOUNT_HISTORY_QUERY = """
query Common_AccountDetails_getAccount($id: UUID!) {
  snapshots: snapshotsForAccount(accountId: $id) {
    date
    signedBalance
  }
}
"""

CREATE_MANUAL_ACCOUNT_MUTATION = """
mutation Web_CreateManualAccount($input: CreateManualAccountMutationInput!) {
  createManualAccount(input: $input) {
    account {
      id
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_ACCOUNT_MUTATION = (
    """
mutation Common_UpdateAccount($input: UpdateAccountMutationInput!) {
  updateAccount(input: $input) {
    account {
      ...AccountFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + ACCOUNT_FIELDS
)

DELETE_ACCOUNT_MUTATION = """
mutation Common_DeleteAccount($id: UUID!) {
  deleteAccount(id: $id) {
    deleted
    errors {
      message
      code
    }
  }
}
"""

def list_accounts(
    session: AuthSession,
    *,
    filters: AccountFilter | None = None,
    include_hidden: bool = False,
) -> list[Account]:
    if filters is None:
        filter_payload = AccountFilter(include_hidden=include_hidden).to_api()
    else:
        filter_payload = filters.to_api()
    if include_hidden and "includeHidden" not in filter_payload:
        filter_payload["includeHidden"] = True

    data = graphql_request(
        session,
        "Common_GetAccounts",
        LIST_ACCOUNTS_QUERY,
        {"filters": filter_payload},
    )
    accounts = data.get("accounts")
    if not isinstance(accounts, list):
        return []
    return [Account.from_api(account) for account in accounts if isinstance(account, dict)]


def get_account(session: AuthSession, account_id: str) -> Account | None:
    data = graphql_request(
        session,
        "Common_GetAccount",
        GET_ACCOUNT_QUERY,
        {"id": account_id},
    )
    account = data.get("account")
    if not isinstance(account, dict):
        return None
    return Account.from_api(account)


def get_net_worth_performance(
    session: AuthSession,
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    account_filter: AccountFilter | None = None,
    use_adaptive_granularity: bool | None = None,
) -> list[NetWorthSnapshot]:
    filter_payload: JsonDict = {
        "startDate": _date_value(start_date),
        "endDate": _date_value(end_date),
        "accountFilters": account_filter.to_api() if account_filter is not None else None,
        "useAdaptiveGranularity": use_adaptive_granularity,
    }
    data = graphql_request(
        session,
        "Common_GetAggregateSnapshots",
        GET_NET_WORTH_PERFORMANCE_QUERY,
        {"filters": _clean(filter_payload)},
    )
    snapshots = data.get("aggregateSnapshots")
    if not isinstance(snapshots, list):
        return []
    return [
        NetWorthSnapshot.from_api(snapshot)
        for snapshot in snapshots
        if isinstance(snapshot, dict)
    ]


def get_net_worth_breakdown(
    session: AuthSession,
    start_date: date | str,
    timeframe: str,
    *,
    filters: AccountFilter | None = None,
) -> list[NetWorthBreakdownPoint]:
    data = graphql_request(
        session,
        "Common_GetSnapshotsByAccountType",
        GET_NET_WORTH_BREAKDOWN_QUERY,
        {
            "startDate": _date_value(start_date),
            "timeframe": timeframe,
            "filters": filters.to_api() if filters is not None else {},
        },
    )
    account_groups = _account_type_groups(data.get("accountTypes"))
    snapshots = data.get("snapshotsByAccountType")
    if not isinstance(snapshots, list):
        return []
    return [
        NetWorthBreakdownPoint.from_api(
            snapshot,
            account_group=account_groups.get(str(snapshot.get("accountType"))),
        )
        for snapshot in snapshots
        if isinstance(snapshot, dict)
    ]


def get_historical_balances(
    session: AuthSession,
    balance_date: date | str,
    *,
    filters: AccountFilter | None = None,
) -> list[AccountBalance]:
    data = graphql_request(
        session,
        "Common_GetDisplayBalanceAtDate",
        GET_HISTORICAL_BALANCE_QUERY,
        {
            "date": _date_value(balance_date),
            "filters": filters.to_api() if filters is not None else {},
        },
    )
    accounts = data.get("accounts")
    if not isinstance(accounts, list):
        return []
    return [
        AccountBalance.from_api(account)
        for account in accounts
        if isinstance(account, dict)
    ]


def get_account_history(
    session: AuthSession,
    account_id: str,
) -> list[AccountHistoryPoint]:
    data = graphql_request(
        session,
        "Common_AccountDetails_getAccount",
        GET_ACCOUNT_HISTORY_QUERY,
        {"id": account_id},
    )
    snapshots = data.get("snapshots")
    if not isinstance(snapshots, list):
        return []
    return [
        AccountHistoryPoint.from_api(snapshot, account_id=account_id)
        for snapshot in snapshots
        if isinstance(snapshot, dict)
    ]


def _account_type_groups(account_types: object) -> dict[str, str]:
    if not isinstance(account_types, list):
        return {}
    return {
        str(account_type["name"]): str(account_type["group"])
        for account_type in account_types
        if isinstance(account_type, dict)
        and account_type.get("name") is not None
        and account_type.get("group") is not None
    }


def create_manual_account(
    session: AuthSession,
    *,
    name: str,
    type: str,
    subtype: str,
    balance: float | None = None,
    include_in_net_worth: bool = True,
    owner_user_id: str | None = None,
) -> str:
    data = graphql_request(
        session,
        "Web_CreateManualAccount",
        CREATE_MANUAL_ACCOUNT_MUTATION,
        {
            "input": _clean(
                {
                    "name": name,
                    "type": type,
                    "subtype": subtype,
                    "currentBalance": balance,
                    "displayBalance": balance,
                    "includeInNetWorth": include_in_net_worth,
                    "ownerUserId": owner_user_id,
                }
            )
        },
    )
    payload = _payload(data, "createManualAccount")
    _raise_payload_errors(payload)
    created_account = payload.get("account")
    if not isinstance(created_account, dict) or not created_account.get("id"):
        raise MonarchError("Monarch did not return the created account id.")
    return str(created_account["id"])


def update_account(
    session: AuthSession,
    account_id: str,
    *,
    name: str | None = None,
    type: str | None = None,
    subtype: str | None = None,
    balance: float | None = None,
    include_in_net_worth: bool | None = None,
    hide_from_list: bool | None = None,
    hide_transactions_from_reports: bool | None = None,
    owner_user_id: str | None = None,
    deactivated_at: date | str | None = None,
) -> Account:
    data = graphql_request(
        session,
        "Common_UpdateAccount",
        UPDATE_ACCOUNT_MUTATION,
        {
            "input": _clean(
                {
                    "id": account_id,
                    "name": name,
                    "type": type,
                    "subtype": subtype,
                    "currentBalance": balance,
                    "displayBalance": balance,
                    "includeInNetWorth": include_in_net_worth,
                    "hideFromList": hide_from_list,
                    "hideTransactionsFromReports": hide_transactions_from_reports,
                    "ownerUserId": owner_user_id,
                    "deactivatedAt": _date_value(deactivated_at),
                }
            )
        },
    )
    result = _payload(data, "updateAccount")
    _raise_payload_errors(result)
    account = result.get("account")
    if not isinstance(account, dict):
        raise MonarchError("Monarch did not return the updated account.")
    return Account.from_api(account)


def delete_account(session: AuthSession, account_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteAccount",
        DELETE_ACCOUNT_MUTATION,
        {"id": account_id},
    )
    payload = _payload(data, "deleteAccount")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


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
        messages = [
            str(error.get("message") or error)
            for error in errors
            if isinstance(error, dict) or error
        ]
        raise MonarchError("; ".join(messages) or "Monarch request failed.")
    if isinstance(errors, dict):
        raise MonarchError(str(errors.get("message") or errors))
    raise MonarchError(str(errors))


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _date_value(value: date | str | None) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    return value
