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
    delete_transaction_attachment,
    download_transaction_attachment,
    get_transaction_attachment,
    list_transaction_attachments,
    load_session,
    upload_transaction_attachment,
)


def main() -> None:
    parser = ArgumentParser(
        description="Demo transaction attachment list/upload/download/delete flows."
    )
    parser.add_argument("--transaction-id", help="Transaction ID for list/upload.")
    parser.add_argument("--upload", type=Path, help="File to upload to --transaction-id.")
    parser.add_argument("--filename", help="Override uploaded filename.")
    parser.add_argument("--attachment-id", help="Attachment ID for get/download/delete.")
    parser.add_argument("--download", type=Path, help="Write attachment bytes to this path.")
    parser.add_argument("--delete", action="store_true", help="Delete --attachment-id.")
    parser.add_argument(
        "--confirm-delete",
        action="store_true",
        help="Required with --delete so deletion is intentional.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.upload:
        if not args.transaction_id:
            raise SystemExit("--upload requires --transaction-id.")
        attachment = upload_transaction_attachment(
            session,
            args.transaction_id,
            args.upload,
            filename=args.filename,
        )
        print("Uploaded attachment:")
        print_attachment(attachment)
        return

    if args.download:
        if not args.attachment_id:
            raise SystemExit("--download requires --attachment-id.")
        data = download_transaction_attachment(session, args.attachment_id, args.download)
        print(f"Downloaded {len(data):,} bytes to {args.download}.")
        return

    if args.delete:
        if not args.attachment_id:
            raise SystemExit("--delete requires --attachment-id.")
        if not args.confirm_delete:
            raise SystemExit("--delete requires --confirm-delete.")
        deleted = delete_transaction_attachment(session, args.attachment_id)
        print(f"Deleted: {'yes' if deleted else 'no'}")
        return

    if args.attachment_id:
        attachment = get_transaction_attachment(session, args.attachment_id)
        if attachment is None:
            raise SystemExit("Attachment not found.")
        print_attachment(attachment)
        return

    if not args.transaction_id:
        raise SystemExit("Provide --transaction-id to list attachments.")

    attachments = list_transaction_attachments(session, args.transaction_id)
    print(f"Attachments: {len(attachments)}")
    for attachment in attachments:
        print_attachment(attachment)


def print_attachment(attachment) -> None:
    print(f"ID: {attachment.id}")
    print(f"Filename: {attachment.filename or ''}")
    print(f"Extension: {attachment.extension or ''}")
    print(f"Size: {format_size(attachment.size_bytes)}")
    print(f"URL: {attachment.original_asset_url or ''}")
    print()


def format_size(value: int | None) -> str:
    if value is None:
        return ""
    return f"{value:,} bytes"


if __name__ == "__main__":
    main()
