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

from monarch_api import get_merchant, list_merchants, load_session  # noqa: E402
from monarch_api.types import MerchantSort  # noqa: E402


def main() -> None:
    parser = ArgumentParser(description="Show Monarch merchants using demo/session.json.")
    parser.add_argument("--search", help="Only show merchants matching this search text.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number to fetch.")
    parser.add_argument("--offset", type=int, help="Offset for paging through merchants.")
    parser.add_argument(
        "--order-by",
        choices=[sort.value for sort in MerchantSort],
        default=MerchantSort.TRANSACTION_COUNT.value,
        help="Backend ordering to request.",
    )
    parser.add_argument("--merchant-id", help="Print details for one merchant.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.merchant_id:
        merchant = get_merchant(session, args.merchant_id)
        if merchant is None:
            raise SystemExit("Merchant not found.")
        print_merchant(merchant)
        return

    merchants = list_merchants(
        session,
        search=args.search,
        limit=args.limit,
        offset=args.offset,
        sort=MerchantSort(args.order_by),
    )

    print(f"Found {len(merchants)} merchants.\n")
    print(f"{'Name':36} {'Transactions':>12} {'Created':12} {'Recurring':>9}")
    print("-" * 74)
    for merchant in merchants:
        print(
            f"{clip(merchant.name, 36):36} "
            f"{format_int(merchant.transaction_count):>12} "
            f"{format_date(merchant.created_at):12} "
            f"{format_bool(merchant.recurring_id is not None):>9}"
        )


def print_merchant(merchant) -> None:
    print(f"Name: {merchant.name}")
    print(f"ID: {merchant.id}")
    print(f"Logo URL: {merchant.logo_url or ''}")
    print(f"Transaction count: {format_int(merchant.transaction_count)}")
    print(f"Rule count: {format_int(merchant.rule_count)}")
    print(f"Can be deleted: {format_bool(merchant.can_be_deleted)}")
    print(f"Recurring ID: {merchant.recurring_id or ''}")
    print(f"Created at: {merchant.created_at or ''}")


def format_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(value)


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def format_date(value: str | None) -> str:
    if not value:
        return ""
    return value[:10]


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
