from __future__ import annotations

import sys
from argparse import ArgumentParser
from calendar import monthrange
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    CashflowBreakdownDirection,
    CashflowBreakdownGroup,
    CashflowFilter,
    CashflowInterval,
    get_cashflow_breakdown,
    get_cashflow_summary,
    get_cashflow_trends,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch cashflow data using demo/session.json.")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    parser.add_argument(
        "--interval",
        choices=[interval.value for interval in CashflowInterval],
        default=CashflowInterval.MONTH.value,
        help="Trend interval.",
    )
    parser.add_argument(
        "--group-by",
        choices=[group.value for group in CashflowBreakdownGroup],
        default=CashflowBreakdownGroup.CATEGORY.value,
        help="Breakdown grouping.",
    )
    parser.add_argument("--account-id", action="append", help="Filter by account ID.")
    parser.add_argument("--category-id", action="append", help="Filter by category ID.")
    parser.add_argument("--category-group-id", action="append", help="Filter by category group ID.")
    parser.add_argument("--merchant-id", action="append", help="Filter by merchant ID.")
    parser.add_argument("--tag-id", action="append", help="Filter by tag ID.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden transactions.")
    parser.add_argument("--limit", type=int, default=10, help="Rows to print per breakdown.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    start_date, end_date = date_range(args.start_date, args.end_date)
    filters = CashflowFilter(
        account_ids=args.account_id,
        category_ids=args.category_id,
        category_group_ids=args.category_group_id,
        merchant_ids=args.merchant_id,
        tag_ids=args.tag_id,
        include_hidden=args.include_hidden,
    )

    session = load_session(SESSION_PATH)
    summary = get_cashflow_summary(session, start_date, end_date, filters=filters)
    trends = get_cashflow_trends(
        session,
        start_date,
        end_date,
        interval=CashflowInterval(args.interval),
        filters=filters,
    )
    income = get_cashflow_breakdown(
        session,
        start_date,
        end_date,
        CashflowBreakdownDirection.INCOME,
        group_by=CashflowBreakdownGroup(args.group_by),
        filters=filters,
    )
    expenses = get_cashflow_breakdown(
        session,
        start_date,
        end_date,
        CashflowBreakdownDirection.EXPENSES,
        group_by=CashflowBreakdownGroup(args.group_by),
        filters=filters,
    )

    print(f"Cashflow from {start_date} to {end_date}\n")
    print_summary(summary)
    print_trends(trends)
    print_breakdown("Income", income.rows[: args.limit])
    print_breakdown("Expenses", expenses.rows[: args.limit])


def date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    today = date.today()
    default_start = today.replace(day=1)
    default_end = today.replace(day=monthrange(today.year, today.month)[1])
    return start_date or default_start.isoformat(), end_date or default_end.isoformat()


def print_summary(summary) -> None:
    print("Summary")
    print(f"  Income:       {format_money(summary.income)}")
    print(f"  Expenses:     {format_money(summary.expenses)}")
    print(f"  Savings:      {format_money(summary.savings)}")
    print(f"  Savings rate: {format_percent(summary.savings_rate)}")


def print_trends(trends) -> None:
    print("\nTrends")
    print(f"{'Period':12} {'Income':>14} {'Expenses':>14} {'Savings':>14} {'Rate':>8}")
    print("-" * 68)
    for point in trends[-12:]:
        print(
            f"{point.label[:12]:12} "
            f"{format_money(point.income):>14} "
            f"{format_money(point.expenses):>14} "
            f"{format_money(point.savings):>14} "
            f"{format_percent(point.savings_rate):>8}"
        )


def print_breakdown(title: str, rows) -> None:
    print(f"\n{title}")
    print(f"{'Name':36} {'Amount':>14} {'Percent':>8} {'Count':>7}")
    print("-" * 70)
    for row in rows:
        print(
            f"{clip(row.name, 36):36} "
            f"{format_money(row.amount):>14} "
            f"{format_percent(row.percent):>8} "
            f"{format_count(row.transaction_count):>7}"
        )


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}%"


def format_count(value: int | None) -> str:
    if value is None:
        return ""
    return str(value)


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
