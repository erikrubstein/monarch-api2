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
    ReceiptFilter,
    ReceiptStatus,
    get_receipt,
    get_receipt_settings,
    list_receipts,
    load_session,
    match_receipt,
    unmatch_receipt,
    update_receipt_settings,
    upload_receipt,
)


def main() -> None:
    parser = ArgumentParser(
        description="Show Monarch receipts using demo/session.json."
    )
    parser.add_argument("--receipt-id", help="Show one receipt.")
    parser.add_argument("--limit", type=int, default=10, help="Rows to print.")
    parser.add_argument("--offset", type=int, default=0, help="List offset.")
    parser.add_argument(
        "--status",
        choices=[status.value for status in ReceiptStatus],
        help="Filter receipts by status.",
    )
    parser.add_argument(
        "--settings",
        action="store_true",
        help="Show receipt settings.",
    )
    parser.add_argument(
        "--set-auto-categorize",
        choices=["true", "false"],
        help="Update receipt auto-categorization.",
    )
    parser.add_argument(
        "--set-update-notes",
        choices=["true", "false"],
        help="Update whether receipts update transaction notes.",
    )
    parser.add_argument(
        "--match-transaction-id",
        help="Match --receipt-id to transaction.",
    )
    parser.add_argument("--unmatch", action="store_true", help="Unmatch --receipt-id.")
    parser.add_argument("--upload", type=Path, help="Try receipt upload flow.")
    parser.add_argument(
        "--upload-filename",
        help="Override the uploaded receipt filename.",
    )
    parser.add_argument(
        "--content-type",
        help="Override the uploaded receipt content type.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.upload:
        receipt = upload_receipt(
            session,
            args.upload,
            filename=args.upload_filename,
            content_type=args.content_type,
        )
        print_receipt_detail(receipt)
        return

    if args.set_auto_categorize is not None or args.set_update_notes is not None:
        settings = update_receipt_settings(
            session,
            auto_categorize=parse_bool(args.set_auto_categorize),
            update_transaction_notes=parse_bool(args.set_update_notes),
        )
        print_settings(settings)
        return

    if args.settings:
        print_settings(get_receipt_settings(session))
        return

    if args.match_transaction_id:
        if not args.receipt_id:
            raise SystemExit("--match-transaction-id requires --receipt-id.")
        receipt = match_receipt(session, args.receipt_id, args.match_transaction_id)
        print_receipt_detail(receipt)
        return

    if args.unmatch:
        if not args.receipt_id:
            raise SystemExit("--unmatch requires --receipt-id.")
        receipt = unmatch_receipt(session, args.receipt_id)
        print_receipt_detail(receipt)
        return

    if args.receipt_id:
        receipt = get_receipt(session, args.receipt_id)
        if receipt is None:
            raise SystemExit("Receipt not found.")
        print_receipt_detail(receipt)
        return

    filters = (
        ReceiptFilter(status=ReceiptStatus(args.status)) if args.status else None
    )
    page = list_receipts(
        session,
        filters=filters,
        limit=args.limit,
        offset=args.offset,
    )
    print(f"Receipts: {len(page.receipts)} of {page.total_count}")
    print_receipt_table(page.receipts)


def print_receipt_table(receipts) -> None:
    if not receipts:
        return
    print(f"{'ID':36} {'Date':10} {'Merchant':28} {'Total':>12} {'Matched':>7}")
    print("-" * 100)
    for receipt in receipts:
        order = receipt.order
        print(
            f"{receipt.id:36} "
            f"{(order.date if order else '') or '':10} "
            f"{clip((order.merchant_name if order else '') or '', 28):28} "
            f"{format_money(order.grand_total if order else None):>12} "
            f"{format_bool(receipt.is_matched):>7}"
        )


def print_receipt_detail(receipt) -> None:
    print(f"ID: {receipt.id}")
    print(f"Status: {receipt.status.value if receipt.status else ''}")
    print(f"Matched transaction: {receipt.transaction_id or ''}")
    if receipt.attachment is not None:
        print(f"Attachment: {receipt.attachment.filename or receipt.attachment.id}")
        print(f"Attachment URL: {receipt.attachment.original_asset_url or ''}")
    if receipt.order is None:
        return
    order = receipt.order
    print(f"Merchant: {order.merchant_name or ''}")
    print(f"Date: {order.date or ''}")
    print(f"Subtotal: {format_money(order.total_before_tax)}")
    print(f"Tax: {format_money(order.tax)}")
    print(f"Tip: {format_money(order.tip)}")
    print(f"Total: {format_money(order.grand_total)}")
    print(f"Line items: {len(order.line_items)}")
    for line_item in order.line_items:
        category = line_item.category.name if line_item.category else ""
        print(
            f"  - {clip(line_item.title, 42):42} "
            f"{format_money(line_item.total):>10} {category}"
        )


def print_settings(settings) -> None:
    print(f"Auto categorize: {format_bool(settings.auto_categorize)}")
    print(f"Update transaction notes: {format_bool(settings.update_transaction_notes)}")


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "true"


def clip(value: str, width: int) -> str:
    return value if len(value) <= width else value[: width - 3] + "..."


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    return f"${value:,.2f}"


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


if __name__ == "__main__":
    main()
