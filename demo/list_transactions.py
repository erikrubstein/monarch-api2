from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    get_transaction,
    get_transaction_splits,
    list_transactions,
    load_session,
)
from monarch_api.types import (  # noqa: E402
    TransactionFilter,
    TransactionSort,
    TransactionVisibility,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch transactions using demo/session.json.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number to fetch.")
    parser.add_argument("--offset", type=int, default=0, help="Offset for paging.")
    parser.add_argument("--search", help="Search text for merchant/name/notes.")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    parser.add_argument("--account-id", action="append", help="Filter by account ID.")
    parser.add_argument("--category-id", action="append", help="Filter by category ID.")
    parser.add_argument("--merchant-id", action="append", help="Filter by merchant ID.")
    parser.add_argument("--tag-id", action="append", help="Filter by tag ID.")
    parser.add_argument("--needs-review", action="store_true", help="Only show transactions needing review.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden transactions.")
    parser.add_argument(
        "--sort",
        choices=[sort.value for sort in TransactionSort],
        default=TransactionSort.DATE_DESCENDING.value,
        help="Backend ordering to request.",
    )
    parser.add_argument("--transaction-id", help="Print details for one transaction.")
    parser.add_argument(
        "--splits",
        action="store_true",
        help="When used with --transaction-id, print the transaction's split rows.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.transaction_id:
        if args.splits:
            details = get_transaction_splits(session, args.transaction_id)
            if details is None:
                raise SystemExit("Transaction not found.")
            print_transaction(details.transaction)
            print_splits(details.splits)
        else:
            transaction = get_transaction(session, args.transaction_id)
            if transaction is None:
                raise SystemExit("Transaction not found.")
            print_transaction(transaction)
        return

    filters = TransactionFilter(
        search=args.search,
        start_date=args.start_date,
        end_date=args.end_date,
        account_ids=args.account_id,
        category_ids=args.category_id,
        merchant_ids=args.merchant_id,
        tag_ids=args.tag_id,
        needs_review=True if args.needs_review else None,
        transaction_visibility=(
            TransactionVisibility.ALL
            if args.include_hidden
            else TransactionVisibility.VISIBLE_ONLY
        ),
    )
    page = list_transactions(
        session,
        filters=filters,
        limit=args.limit,
        offset=args.offset,
        sort=TransactionSort(args.sort),
    )

    print(
        f"Showing {len(page.transactions)} of {page.total_count} transactions "
        f"(offset {page.offset}).\n"
    )
    print(f"{'Date':10} {'Amount':>12} {'Merchant':32} {'Category':24} {'Tags':24}")
    print("-" * 108)
    for transaction in page.transactions:
        print(
            f"{transaction.date[:10]:10} "
            f"{format_amount(transaction.amount):>12} "
            f"{clip(transaction.merchant_name, 32):32} "
            f"{clip(category_name(transaction), 24):24} "
            f"{clip(tag_names(transaction), 24):24}"
        )


def print_transaction(transaction) -> None:
    print(f"ID: {transaction.id}")
    print(f"Date: {transaction.date}")
    print(f"Amount: {format_amount(transaction.amount)}")
    print(f"Merchant: {transaction.merchant_name}")
    print(f"Original statement: {transaction.original_statement or ''}")
    print(f"Account: {transaction.account.display_name if transaction.account else ''}")
    print(f"Category: {category_name(transaction)}")
    print(f"Tags: {tag_names(transaction)}")
    print(f"Notes: {transaction.notes or ''}")
    print(f"Pending: {format_bool(transaction.pending)}")
    print(f"Needs review: {format_bool(transaction.needs_review)}")
    print(f"Review status: {transaction.review_status.value if transaction.review_status else ''}")
    print(f"Hidden from reports: {format_bool(transaction.hide_from_reports)}")
    print(f"Recurring ID: {transaction.recurring_id or ''}")
    print(f"Original transaction ID: {transaction.original_transaction_id or ''}")
    print(f"Has splits: {format_bool(transaction.has_splits)}")
    print(f"Is split row: {format_bool(transaction.is_split)}")
    print(f"Attachment count: {transaction.attachment_count}")
    for attachment in transaction.attachments:
        print(
            "  "
            f"{attachment.id} "
            f"{attachment.filename or ''} "
            f"{format_size(attachment.size_bytes)}"
        )
    print(f"Owner: {transaction.owner.display_name if transaction.owner else ''}")
    print(f"Updated at: {transaction.updated_at or ''}")


def print_splits(splits) -> None:
    print(f"\nSplits: {len(splits)}")
    if not splits:
        return
    print(f"{'Amount':>12} {'Merchant':32} {'Category':24} {'Tags':24}")
    print("-" * 96)
    for split in splits:
        print(
            f"{format_amount(split.amount):>12} "
            f"{clip(split.merchant_name, 32):32} "
            f"{clip(category_name(split), 24):24} "
            f"{clip(tag_names(split), 24):24}"
        )


def category_name(transaction) -> str:
    if transaction.category is None:
        return ""
    return transaction.category.name


def tag_names(transaction) -> str:
    return ", ".join(tag.name for tag in transaction.tags or [])


def format_amount(value: float) -> str:
    return f"${value:,.2f}"


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def format_size(value: int | None) -> str:
    if value is None:
        return ""
    return f"{value:,} bytes"


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
