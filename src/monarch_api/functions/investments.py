from __future__ import annotations

from datetime import date

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.investments import (
    Holding,
    InvestmentAccount,
    InvestmentPerformance,
    Portfolio,
    Security,
)


INVESTMENT_ACCOUNT_FIELDS = """
fragment InvestmentAccountFields on Account {
  id
  displayName
  isTaxable
  icon
  order
  logoUrl
  includeInNetWorth
  syncDisabled
  subtype {
    display
  }
}
"""

SECURITY_FIELDS = """
fragment InvestmentSecurityFields on Security {
  id
  name
  logo
  ticker
  type
  typeDisplay
  currentPrice
  currentPriceUpdatedAt
  closingPrice
  closingPriceUpdatedAt
  oneDayChangeDollars
  oneDayChangePercent
  categoryGroup
  morningstarCategory
  globalCategory
  broadAssetClass
  legalStructure
  prospectusObjective
  aggregatedCategory
  indexStrategy
}
"""

HOLDING_FIELDS = (
    """
fragment InvestmentHoldingFields on Holding {
  id
  type
  typeDisplay
  name
  ticker
  closingPrice
  isManual
  closingPriceUpdatedAt
  costBasis
  userCostBasis
  quantity
  value
  account {
    id
    displayName
    icon
    logoUrl
  }
  taxLots {
    id
    createdAt
    acquisitionDate
    acquisitionQuantity
    costBasisPerUnit
  }
}
"""
)

AGGREGATE_HOLDING_FIELDS = (
    """
fragment InvestmentAggregateHoldingFields on AggregateHolding {
  id
  quantity
  costBasis
  totalValue
  securityPriceChangeDollars
  securityPriceChangePercent
  lastSyncedAt
  holdings {
    ...InvestmentHoldingFields
  }
  security {
    ...InvestmentSecurityFields
  }
}
"""
    + HOLDING_FIELDS
    + SECURITY_FIELDS
)

PORTFOLIO_FIELDS = (
    """
fragment InvestmentPortfolioFields on Portfolio {
  performance {
    totalValue
    totalChangePercent
    totalChangeDollars
    oneDayChangeDollars
    oneDayChangePercent
    topMovers {
      ...InvestmentSecurityFields
    }
    historicalChart {
      date
      returnPercent
      value
    }
    benchmarks {
      security {
        ...InvestmentSecurityFields
      }
      historicalChart {
        date
        returnPercent
        value
      }
    }
  }
  aggregateHoldings {
    edges {
      node {
        ...InvestmentAggregateHoldingFields
      }
    }
  }
}
"""
    + AGGREGATE_HOLDING_FIELDS
)

LIST_INVESTMENT_ACCOUNTS_QUERY = (
    """
query Web_GetInvestmentsAccounts {
  accounts(
    filters: {
      accountType: "brokerage"
      includeManual: true
      includeHidden: false
      ignoreHiddenFromNetWorth: true
    }
  ) {
    ...InvestmentAccountFields
  }
}
"""
    + INVESTMENT_ACCOUNT_FIELDS
)

GET_PORTFOLIO_QUERY = (
    """
query Web_GetPortfolio($portfolioInput: PortfolioInput) {
  portfolio(input: $portfolioInput) {
    ...InvestmentPortfolioFields
  }
}
"""
    + PORTFOLIO_FIELDS
)

LIST_HOLDINGS_QUERY = (
    """
query Web_GetHoldings($input: PortfolioInput) {
  portfolio(input: $input) {
    aggregateHoldings {
      edges {
        node {
          ...InvestmentAggregateHoldingFields
        }
      }
    }
  }
}
"""
    + AGGREGATE_HOLDING_FIELDS
)

SEARCH_SECURITIES_QUERY = (
    """
query Web_SearchSecurities(
  $limit: Int
  $orderByPopularity: Boolean
  $search: String
) {
  securities(
    limit: $limit
    orderByPopularity: $orderByPopularity
    search: $search
  ) {
    ...InvestmentSecurityFields
  }
}
"""
    + SECURITY_FIELDS
)

GET_SECURITY_QUERY = (
    """
query GetHoldingDetailsFormSecurityDetails($id: ID!) {
  security(id: $id) {
    ...InvestmentSecurityFields
  }
}
"""
    + SECURITY_FIELDS
)

GET_HOLDING_PERFORMANCE_QUERY = (
    """
query Web_GetInvestmentsHoldingDrawerHistoricalPerformance(
  $input: SecurityHistoricalPerformanceInput!
) {
  securityHistoricalPerformance(input: $input) {
    security {
      ...InvestmentSecurityFields
    }
    historicalChart {
      date
      returnPercent
      value
    }
  }
}
"""
    + SECURITY_FIELDS
)

CREATE_MANUAL_HOLDING_MUTATION = """
mutation Common_CreateManualHolding($input: CreateManualHoldingInput!) {
  createManualHolding(input: $input) {
    holding {
      id
      ticker
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_HOLDING_MUTATION = """
mutation Common_UpdateHolding($input: UpdateHoldingInput!) {
  updateHolding(input: $input) {
    holding {
      id
    }
    errors {
      message
      code
    }
  }
}
"""

DELETE_HOLDING_MUTATION = """
mutation Common_DeleteHolding($id: ID!) {
  deleteHolding(id: $id) {
    deleted
    errors {
      message
      code
    }
  }
}
"""


def list_investment_accounts(session: AuthSession) -> list[InvestmentAccount]:
    data = graphql_request(
        session,
        "Web_GetInvestmentsAccounts",
        LIST_INVESTMENT_ACCOUNTS_QUERY,
    )
    accounts = data.get("accounts")
    if not isinstance(accounts, list):
        return []
    return [
        InvestmentAccount.from_api(account)
        for account in accounts
        if isinstance(account, dict)
    ]


def get_portfolio(
    session: AuthSession,
    *,
    account_ids: list[str] | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    include_hidden_holdings: bool | None = None,
    top_movers_limit: int | None = None,
) -> Portfolio:
    data = graphql_request(
        session,
        "Web_GetPortfolio",
        GET_PORTFOLIO_QUERY,
        {
            "portfolioInput": _portfolio_input(
                account_ids=account_ids,
                start_date=start_date,
                end_date=end_date,
                include_hidden_holdings=include_hidden_holdings,
                top_movers_limit=top_movers_limit,
            )
        },
    )
    portfolio = data.get("portfolio")
    if not isinstance(portfolio, dict):
        raise MonarchError("Monarch did not return a portfolio.")
    return Portfolio.from_api(portfolio)


def list_holdings(
    session: AuthSession,
    *,
    account_ids: list[str] | None = None,
    include_hidden_holdings: bool | None = None,
) -> list[Holding]:
    data = graphql_request(
        session,
        "Web_GetHoldings",
        LIST_HOLDINGS_QUERY,
        {
            "input": _portfolio_input(
                account_ids=account_ids,
                include_hidden_holdings=include_hidden_holdings,
            )
        },
    )
    portfolio = data.get("portfolio")
    if not isinstance(portfolio, dict):
        return []
    return Portfolio.from_api(portfolio).holdings


def get_holding(session: AuthSession, holding_id: str) -> Holding | None:
    for holding in list_holdings(session):
        if holding.id == holding_id or holding.aggregate_id == holding_id:
            return holding
    return None


def search_securities(
    session: AuthSession,
    query: str,
    *,
    limit: int = 20,
    order_by_popularity: bool = True,
) -> list[Security]:
    data = graphql_request(
        session,
        "Web_SearchSecurities",
        SEARCH_SECURITIES_QUERY,
        {
            "search": query,
            "limit": limit,
            "orderByPopularity": order_by_popularity,
        },
    )
    securities = data.get("securities")
    if not isinstance(securities, list):
        return []
    return [
        security
        for security in (
            Security.from_api(item)
            for item in securities
            if isinstance(item, dict)
        )
        if security is not None
    ]


def get_security(session: AuthSession, security_id: str) -> Security | None:
    data = graphql_request(
        session,
        "GetHoldingDetailsFormSecurityDetails",
        GET_SECURITY_QUERY,
        {"id": security_id},
    )
    security = data.get("security")
    if not isinstance(security, dict):
        return None
    return Security.from_api(security)


def get_holding_performance(
    session: AuthSession,
    holding_id: str,
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> InvestmentPerformance | None:
    holding = get_holding(session, holding_id)
    if holding is None or holding.security is None:
        return None
    data = graphql_request(
        session,
        "Web_GetInvestmentsHoldingDrawerHistoricalPerformance",
        GET_HOLDING_PERFORMANCE_QUERY,
        {
            "input": _clean(
                {
                    "securityIds": [holding.security.id],
                    "startDate": _date_value(start_date),
                    "endDate": _date_value(end_date),
                }
            )
        },
    )
    performances = data.get("securityHistoricalPerformance")
    if not isinstance(performances, list) or not performances:
        return None
    performance = performances[0]
    if not isinstance(performance, dict):
        return None
    return InvestmentPerformance.from_api(performance)


def create_manual_holding(
    session: AuthSession,
    *,
    account_id: str,
    security_id: str,
    quantity: float,
    cost_basis: float | None = None,
) -> Holding:
    data = graphql_request(
        session,
        "Common_CreateManualHolding",
        CREATE_MANUAL_HOLDING_MUTATION,
        {
            "input": {
                "accountId": account_id,
                "securityId": security_id,
                "quantity": quantity,
            }
        },
    )
    payload = _payload(data, "createManualHolding")
    _raise_payload_errors(payload)
    raw_holding = payload.get("holding")
    if not isinstance(raw_holding, dict) or raw_holding.get("id") is None:
        raise MonarchError("Monarch did not return the created holding.")

    holding_id = str(raw_holding["id"])
    if cost_basis is not None:
        return update_manual_holding(
            session,
            holding_id,
            cost_basis=cost_basis,
        )

    holding = get_holding(session, holding_id)
    if holding is None:
        raise MonarchError("Manual holding was created but could not be refetched.")
    return holding


def update_manual_holding(
    session: AuthSession,
    holding_id: str,
    *,
    quantity: float | None = None,
    cost_basis: float | None = None,
    security_type: str | None = None,
) -> Holding:
    data = graphql_request(
        session,
        "Common_UpdateHolding",
        UPDATE_HOLDING_MUTATION,
        {
            "input": _clean(
                {
                    "id": holding_id,
                    "quantity": quantity,
                    "userCostBasis": cost_basis,
                    "securityType": security_type,
                }
            )
        },
    )
    payload = _payload(data, "updateHolding")
    _raise_payload_errors(payload)
    holding = get_holding(session, holding_id)
    if holding is None:
        raise MonarchError("Manual holding was updated but could not be refetched.")
    return holding


def delete_manual_holding(session: AuthSession, holding_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteHolding",
        DELETE_HOLDING_MUTATION,
        {"id": holding_id},
    )
    payload = _payload(data, "deleteHolding")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


def _portfolio_input(
    *,
    account_ids: list[str] | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    include_hidden_holdings: bool | None = None,
    top_movers_limit: int | None = None,
) -> JsonDict:
    return _clean(
        {
            "accountIds": account_ids,
            "startDate": _date_value(start_date),
            "endDate": _date_value(end_date),
            "includeHiddenHoldings": include_hidden_holdings,
            "topMoversLimit": top_movers_limit,
        }
    )


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
