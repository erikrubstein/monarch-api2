"""Unofficial Monarch Money API client."""

from monarch_api.functions.accounts import (
    create_manual_account,
    delete_account,
    get_account,
    get_account_history,
    get_historical_balances,
    get_net_worth_breakdown,
    get_net_worth_performance,
    list_accounts,
    update_account,
)
from monarch_api.functions.auth import create_session, load_session, save_session
from monarch_api.functions.common import (
    MfaRequiredError,
    MonarchAuthError,
    MonarchError,
    MonarchGraphQLError,
    build_auth_headers,
    graphql_request,
    rest_request,
)
from monarch_api.types.accounts import (
    Account,
    AccountBalance,
    AccountFilter,
    AccountHistoryPoint,
    AccountType,
    Institution,
    NetWorthBreakdownPoint,
    NetWorthSnapshot,
)
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import User

__all__ = [
    "Account",
    "AccountBalance",
    "AccountFilter",
    "AccountHistoryPoint",
    "AccountType",
    "AuthSession",
    "Institution",
    "NetWorthBreakdownPoint",
    "MfaRequiredError",
    "MonarchAuthError",
    "MonarchError",
    "MonarchGraphQLError",
    "NetWorthSnapshot",
    "User",
    "build_auth_headers",
    "create_manual_account",
    "create_session",
    "delete_account",
    "get_account",
    "get_account_history",
    "get_historical_balances",
    "get_net_worth_breakdown",
    "get_net_worth_performance",
    "graphql_request",
    "list_accounts",
    "load_session",
    "rest_request",
    "save_session",
    "update_account",
]
