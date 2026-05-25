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
    RecurringFilter,
    RecurringType,
    get_recurring_stream,
    get_recurring_summary,
    list_recurring_occurrences,
    list_recurring_streams,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch recurring data using demo/session.json.")
    parser.add_argument("--recurring-id", help="Print details for one recurring stream.")
    parser.add_argument("--upcoming", action="store_true", help="Show dated recurring occurrences.")
    parser.add_argument("--summary", action="store_true", help="Show recurring summary totals.")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    parser.add_argument("--account-id", action="append", help="Filter by account ID.")
    parser.add_argument("--category-id", action="append", help="Filter by category ID.")
    parser.add_argument("--merchant-id", action="append", help="Filter by merchant ID.")
    parser.add_argument(
        "--type",
        choices=[type_.value for type_ in RecurringType],
        action="append",
        help="Filter by recurring type.",
    )
    parser.add_argument("--frequency", action="append", help="Filter by backend frequency value.")
    parser.add_argument("--exclude-liabilities", action="store_true")
    parser.add_argument("--exclude-pending", action="store_true")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)
    filters = RecurringFilter(
        account_ids=args.account_id,
        category_ids=args.category_id,
        merchant_ids=args.merchant_id,
        recurring_types=args.type,
        frequencies=args.frequency,
    )

    if args.recurring_id:
        stream = get_recurring_stream(
            session,
            args.recurring_id,
            include_liabilities=not args.exclude_liabilities,
        )
        if stream is None:
            raise SystemExit("Recurring stream not found.")
        print_stream(stream)
        return

    start_date, end_date = date_range(args.start_date, args.end_date)
    if args.summary:
        summary = get_recurring_summary(session, start_date, end_date, filters=filters)
        print(f"Recurring summary from {start_date} to {end_date}\n")
        print_summary("Expenses", summary.expense)
        print_summary("Credit cards", summary.credit_card)
        print_summary("Income", summary.income)
        return

    if args.upcoming:
        occurrences = list_recurring_occurrences(
            session,
            start_date,
            end_date,
            filters=filters,
            include_liabilities=not args.exclude_liabilities,
        )
        print(f"Found {len(occurrences)} recurring occurrences from {start_date} to {end_date}.\n")
        print(f"{'Date':10} {'Amount':>12} {'Name':36} {'Account':24} {'Done':>6}")
        print("-" * 95)
        for occurrence in occurrences[: args.limit]:
            print(
                f"{occurrence.date[:10]:10} "
                f"{format_money(occurrence.amount):>12} "
                f"{clip(occurrence.name, 36):36} "
                f"{clip(account_name(occurrence.account), 24):24} "
                f"{format_bool(occurrence.is_completed):>6}"
            )
        return

    streams = list_recurring_streams(
        session,
        filters=filters,
        include_pending=not args.exclude_pending,
        include_liabilities=not args.exclude_liabilities,
    )
    print(f"Found {len(streams)} recurring streams.\n")
    print(f"{'Name':36} {'Frequency':18} {'Next':10} {'Amount':>12} {'Type':12}")
    print("-" * 94)
    for stream in streams[: args.limit]:
        print(
            f"{clip(stream.name, 36):36} "
            f"{clip(stream.frequency or '', 18):18} "
            f"{format_date(stream.next_date):10} "
            f"{format_money(stream.next_amount if stream.next_amount is not None else stream.amount):>12} "
            f"{recurring_type(stream):12}"
        )


def date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    today = date.today()
    default_start = today.replace(day=1)
    default_end = today.replace(day=monthrange(today.year, today.month)[1])
    return start_date or default_start.isoformat(), end_date or default_end.isoformat()


def print_stream(stream) -> None:
    print(f"Name: {stream.name}")
    print(f"ID: {stream.id}")
    print(f"Frequency: {stream.frequency or ''}")
    print(f"Amount: {format_money(stream.amount)}")
    print(f"Next date: {stream.next_date or ''}")
    print(f"Next amount: {format_money(stream.next_amount)}")
    print(f"Base date: {stream.base_date or ''}")
    print(f"Day of month: {stream.day_of_month or ''}")
    print(f"Active: {format_bool(stream.is_active)}")
    print(f"Approximate: {format_bool(stream.is_approximate)}")
    print(f"Type: {recurring_type(stream)}")
    print(f"Merchant: {stream.merchant.name if stream.merchant else ''}")
    print(f"Account: {account_name(stream.account)}")
    print(f"Category: {stream.category.name if stream.category else ''}")


def print_summary(title: str, bucket) -> None:
    print(title)
    print(f"  Completed:            {format_money(bucket.completed)}")
    print(f"  Remaining:            {format_money(bucket.remaining)}")
    print(f"  Total:                {format_money(bucket.total)}")
    print(f"  Count:                {format_count(bucket.count)}")
    print(f"  Pending amount count: {format_count(bucket.pending_amount_count)}")


def account_name(account) -> str:
    if account is None:
        return ""
    return account.display_name


def recurring_type(stream) -> str:
    if stream.recurring_type is None:
        return ""
    return stream.recurring_type.value


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_date(value: str | None) -> str:
    if not value:
        return ""
    return value[:10]


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


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
