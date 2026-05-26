from __future__ import annotations

import sys
from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    get_holding,
    get_holding_performance,
    get_portfolio,
    get_security,
    list_holdings,
    list_investment_accounts,
    load_session,
    search_securities,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch investments using demo/session.json.")
    parser.add_argument("--accounts", action="store_true", help="Show investment accounts.")
    parser.add_argument("--holdings", action="store_true", help="Show holdings.")
    parser.add_argument("--portfolio", action="store_true", help="Show portfolio summary.")
    parser.add_argument("--holding-id", help="Show one holding.")
    parser.add_argument("--security-id", help="Show one security.")
    parser.add_argument("--performance", action="store_true", help="Show holding performance.")
    parser.add_argument("--search", help="Search securities.")
    parser.add_argument("--start-date", help="Performance start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="Performance end date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.search:
        securities = search_securities(session, args.search, limit=args.limit)
        print(f"Found {len(securities)} securities.\n")
        print_securities(securities)
        return

    if args.security_id:
        security = get_security(session, args.security_id)
        if security is None:
            raise SystemExit("Security not found.")
        print_security(security)
        return

    if args.holding_id:
        holding = get_holding(session, args.holding_id)
        if holding is None:
            raise SystemExit("Holding not found.")
        print_holding_detail(holding)
        if args.performance:
            start_date, end_date = date_range(args.start_date, args.end_date)
            performance = get_holding_performance(
                session,
                args.holding_id,
                start_date=start_date,
                end_date=end_date,
            )
            if performance is None:
                print("\nNo performance data.")
            else:
                print(f"\nPerformance points: {len(performance.points)}")
                print_performance(performance.points[: args.limit])
        return

    if args.accounts:
        accounts = list_investment_accounts(session)
        print(f"Found {len(accounts)} investment accounts.\n")
        print_accounts(accounts[: args.limit])

    if args.portfolio or not (args.accounts or args.holdings):
        portfolio = get_portfolio(session)
        print_portfolio(portfolio)

    if args.holdings:
        holdings = list_holdings(session)
        print(f"\nHoldings: {len(holdings)}")
        print_holdings(holdings[: args.limit])


def print_accounts(accounts) -> None:
    if not accounts:
        return
    print(f"{'Name':32} {'Subtype':18} {'Taxable':>7} {'Net Worth':>9}")
    print("-" * 72)
    for account in accounts:
        print(
            f"{clip(account.display_name, 32):32} "
            f"{clip(account.subtype_display or '', 18):18} "
            f"{format_bool(account.is_taxable):>7} "
            f"{format_bool(account.include_in_net_worth):>9}"
        )


def print_portfolio(portfolio) -> None:
    summary = portfolio.summary
    print("Portfolio")
    print(f"  Total value: {format_money(summary.total_value)}")
    print(f"  Total change: {format_money(summary.total_change_dollars)}")
    print(f"  Total change %: {format_percent(summary.total_change_percent)}")
    print(f"  One day change: {format_money(summary.one_day_change_dollars)}")
    print(f"  One day change %: {format_percent(summary.one_day_change_percent)}")
    print(f"  Holdings: {summary.holdings_count}")
    if portfolio.allocations:
        print("\nAllocations")
        print(f"{'Label':28} {'Value':>12} {'Percent':>9}")
        print("-" * 51)
        for allocation in portfolio.allocations:
            print(
                f"{clip(allocation.label, 28):28} "
                f"{format_money(allocation.value):>12} "
                f"{format_percent(allocation.percent_of_portfolio):>9}"
            )


def print_holdings(holdings) -> None:
    if not holdings:
        return
    print(f"{'Ticker':12} {'Name':30} {'Account':24} {'Value':>12} {'Manual':>6}")
    print("-" * 90)
    for holding in holdings:
        print(
            f"{clip(holding.ticker or '', 12):12} "
            f"{clip(holding.name, 30):30} "
            f"{clip(account_name(holding), 24):24} "
            f"{format_money(holding.value):>12} "
            f"{format_bool(holding.is_manual):>6}"
        )


def print_holding_detail(holding) -> None:
    print(f"ID: {holding.id}")
    print(f"Aggregate ID: {holding.aggregate_id or ''}")
    print(f"Ticker: {holding.ticker or ''}")
    print(f"Name: {holding.name}")
    print(f"Type: {holding.type_display or holding.type or ''}")
    print(f"Account: {account_name(holding)}")
    print(f"Quantity: {format_number(holding.quantity)}")
    print(f"Value: {format_money(holding.value)}")
    print(f"Cost basis: {format_money(holding.cost_basis)}")
    print(f"User cost basis: {format_money(holding.user_cost_basis)}")
    print(f"Manual: {format_bool(holding.is_manual)}")


def print_securities(securities) -> None:
    if not securities:
        return
    print(f"{'Ticker':12} {'Name':44} {'Type':18} {'Price':>12}")
    print("-" * 90)
    for security in securities:
        print(
            f"{clip(security.ticker or '', 12):12} "
            f"{clip(security.name, 44):44} "
            f"{clip(security.type_display or security.type or '', 18):18} "
            f"{format_money(security.current_price or security.closing_price):>12}"
        )


def print_security(security) -> None:
    print(f"ID: {security.id}")
    print(f"Ticker: {security.ticker or ''}")
    print(f"Name: {security.name}")
    print(f"Type: {security.type_display or security.type or ''}")
    print(f"Current price: {format_money(security.current_price)}")
    print(f"Closing price: {format_money(security.closing_price)}")
    print(f"One day change: {format_money(security.one_day_change_dollars)}")
    print(f"One day change %: {format_percent(security.one_day_change_percent)}")


def print_performance(points) -> None:
    if not points:
        return
    print(f"{'Date':10} {'Value':>12} {'Return %':>10}")
    print("-" * 36)
    for point in points:
        print(
            f"{point.date[:10]:10} "
            f"{format_money(point.value):>12} "
            f"{format_percent(point.return_percent):>10}"
        )


def date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    today = date.today()
    return (
        start_date or (today - timedelta(days=90)).isoformat(),
        end_date or today.isoformat(),
    )


def account_name(holding) -> str:
    if holding.account is None:
        return ""
    return holding.account.display_name


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}%"


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
