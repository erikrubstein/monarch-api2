from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    ReportGroup,
    ReportSort,
    ReportTimeframe,
    TransactionFilter,
    TransactionVisibility,
    get_report_data,
    get_saved_report,
    list_saved_reports,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch report data using demo/session.json.")
    parser.add_argument(
        "--group-by",
        choices=[group.value for group in ReportGroup],
        default=ReportGroup.CATEGORY.value,
        help="Primary report grouping.",
    )
    parser.add_argument(
        "--timeframe",
        choices=[timeframe.value for timeframe in ReportTimeframe],
        help="Optional time bucket grouping.",
    )
    parser.add_argument(
        "--sort",
        choices=[sort.value for sort in ReportSort],
        help="Backend report sort.",
    )
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    parser.add_argument("--account-id", action="append", help="Filter by account ID.")
    parser.add_argument("--category-id", action="append", help="Filter by category ID.")
    parser.add_argument("--merchant-id", action="append", help="Filter by merchant ID.")
    parser.add_argument("--tag-id", action="append", help="Filter by tag ID.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden transactions.")
    parser.add_argument("--saved", action="store_true", help="List saved reports.")
    parser.add_argument("--saved-report-id", help="Print one saved report.")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.saved_report_id:
        report = get_saved_report(session, args.saved_report_id)
        if report is None:
            raise SystemExit("Saved report not found.")
        print_saved_report(report)
        return

    if args.saved:
        reports = list_saved_reports(session)
        print(f"Found {len(reports)} saved reports.\n")
        print(f"{'Name':36} {'ID':36} {'Groups':24} {'Timeframe':10}")
        print("-" * 112)
        for report in reports:
            print(
                f"{clip(report.name, 36):36} "
                f"{report.id:36} "
                f"{clip(groups(report.group_by), 24):24} "
                f"{timeframe(report.timeframe):10}"
            )
        return

    filters = TransactionFilter(
        start_date=args.start_date,
        end_date=args.end_date,
        account_ids=args.account_id,
        category_ids=args.category_id,
        merchant_ids=args.merchant_id,
        tag_ids=args.tag_id,
        transaction_visibility=(
            TransactionVisibility.ALL
            if args.include_hidden
            else TransactionVisibility.VISIBLE_ONLY
        ),
    )
    report = get_report_data(
        session,
        filters=filters,
        group_by=ReportGroup(args.group_by),
        timeframe=ReportTimeframe(args.timeframe) if args.timeframe else None,
        sort_by=ReportSort(args.sort) if args.sort else None,
    )

    print("Summary")
    print_summary(report.summary)
    print(f"\nRows: {len(report.rows)}\n")
    print(f"{'Group':42} {'Total':>14} {'Income':>14} {'Expenses':>14} {'Count':>7}")
    print("-" * 96)
    for row in report.rows[: args.limit]:
        print(
            f"{clip(row.group.label, 42):42} "
            f"{format_money(row.summary.total):>14} "
            f"{format_money(row.summary.income):>14} "
            f"{format_money(row.summary.expenses):>14} "
            f"{format_count(row.summary.count):>7}"
        )


def print_saved_report(report) -> None:
    print(f"Name: {report.name}")
    print(f"ID: {report.id}")
    print(f"Groups: {groups(report.group_by)}")
    print(f"Timeframe: {timeframe(report.timeframe)}")
    if report.filters is not None:
        print(f"Start date: {report.filters.start_date or ''}")
        print(f"End date: {report.filters.end_date or ''}")
        print(f"Search: {report.filters.search or ''}")


def print_summary(summary) -> None:
    print(f"  Total:        {format_money(summary.total)}")
    print(f"  Income:       {format_money(summary.income)}")
    print(f"  Expenses:     {format_money(summary.expenses)}")
    print(f"  Savings:      {format_money(summary.savings)}")
    print(f"  Savings rate: {format_percent(summary.savings_rate)}")
    print(f"  Count:        {format_count(summary.count)}")


def groups(value) -> str:
    if not value:
        return ""
    return ", ".join(group.value for group in value)


def timeframe(value) -> str:
    if value is None:
        return ""
    return value.value


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
