from __future__ import annotations

from argparse import ArgumentParser
from datetime import date, timedelta
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    create_manual_holding,
    delete_account,
    delete_manual_holding,
    get_holding,
    get_holding_performance,
    get_portfolio,
    get_security,
    graphql_request,
    list_holdings,
    list_investment_accounts,
    load_session,
    search_securities,
    update_manual_holding,
)
from monarch_api.functions.common import MonarchError  # noqa: E402


CREATE_MANUAL_INVESTMENTS_ACCOUNT_MUTATION = """
mutation Common_CreateManualInvestmentsAccount(
  $input: CreateManualInvestmentsAccountInput!
) {
  createManualInvestmentsAccount(input: $input) {
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


def main() -> None:
    parser = ArgumentParser(description="Run live investments API checks.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create and clean up a temporary manual investment account and holding.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    accounts = list_investment_accounts(session)
    assert isinstance(accounts, list)

    portfolio = get_portfolio(session)
    assert portfolio.summary is not None
    assert portfolio.summary.holdings_count == len(portfolio.holdings)

    holdings = list_holdings(session)
    assert len(holdings) == len(portfolio.holdings)

    securities = search_securities(session, "VTI", limit=3)
    assert securities
    assert any(security.ticker for security in securities)

    first_security = get_security(session, securities[0].id)
    assert first_security is not None
    assert first_security.id == securities[0].id

    if holdings:
        holding = get_holding(session, holdings[0].id)
        assert holding is not None
        assert holding.id == holdings[0].id

        performance = get_holding_performance(
            session,
            holding.id,
            start_date=(date.today() - timedelta(days=30)).isoformat(),
            end_date=date.today().isoformat(),
        )
        assert performance is None or isinstance(performance.points, list)

    if args.write:
        run_write_test(session, securities[0].id)

    print("Investments live test passed.")


def run_write_test(session, security_id: str) -> None:
    account_id = None
    holding_id = None
    try:
        account_id = create_temp_manual_investments_account(session)
        holding = create_manual_holding(
            session,
            account_id=account_id,
            security_id=security_id,
            quantity=1.0,
            cost_basis=123.45,
        )
        holding_id = holding.id
        assert holding.quantity == 1.0

        holding = update_manual_holding(
            session,
            holding_id,
            quantity=2.0,
            cost_basis=234.56,
        )
        assert holding.quantity == 2.0

        assert delete_manual_holding(session, holding_id)
        holding_id = None
    finally:
        if holding_id is not None:
            delete_manual_holding(session, holding_id)
        if account_id is not None:
            delete_account(session, account_id)


def create_temp_manual_investments_account(session) -> str:
    data = graphql_request(
        session,
        "Common_CreateManualInvestmentsAccount",
        CREATE_MANUAL_INVESTMENTS_ACCOUNT_MUTATION,
        {
            "input": {
                "name": "Codex API Investments Live Test",
                "subtype": "brokerage",
                "manualInvestmentsTrackingMethod": "holdings",
                "initialHoldings": [],
            }
        },
    )
    payload = data.get("createManualInvestmentsAccount")
    if not isinstance(payload, dict):
        raise MonarchError("Monarch did not return the created investment account.")
    errors = payload.get("errors")
    if errors:
        raise MonarchError(str(errors))
    account = payload.get("account")
    if not isinstance(account, dict) or account.get("id") is None:
        raise MonarchError("Monarch did not return the created investment account id.")
    return str(account["id"])


if __name__ == "__main__":
    main()
