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

from monarch_api import get_tag, list_tags, load_session  # noqa: E402


def main() -> None:
    parser = ArgumentParser(description="Show Monarch tags using demo/session.json.")
    parser.add_argument("--search", help="Only show tags matching this search text.")
    parser.add_argument("--limit", type=int, help="Maximum number of tags to fetch.")
    parser.add_argument(
        "--include-counts",
        action="store_true",
        help="Include transaction counts for each tag.",
    )
    parser.add_argument("--tag-id", help="Print details for one tag.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.tag_id:
        tag = get_tag(session, args.tag_id)
        if tag is None:
            raise SystemExit("Tag not found.")
        print_tag(tag)
        return

    tags = list_tags(
        session,
        search=args.search,
        limit=args.limit,
        include_transaction_count=args.include_counts,
    )

    print(f"Found {len(tags)} tags.\n")
    print(f"{'Name':32} {'Color':10} {'Order':>5} {'Transactions':>12}")
    print("-" * 64)
    for tag in tags:
        print(
            f"{clip(tag.name, 32):32} "
            f"{tag.color or '':10} "
            f"{format_int(tag.order):>5} "
            f"{format_int(tag.transaction_count):>12}"
        )


def print_tag(tag) -> None:
    print(f"Name: {tag.name}")
    print(f"ID: {tag.id}")
    print(f"Color: {tag.color or ''}")
    print(f"Order: {format_int(tag.order)}")
    print(f"Transaction count: {format_int(tag.transaction_count)}")


def format_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(value)


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
