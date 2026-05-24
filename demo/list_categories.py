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
    CategoryFilter,
    CategoryType,
    get_category,
    get_category_catalog,
    get_category_group,
    list_categories,
    list_category_groups,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch category data using demo/session.json.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument(
        "--type",
        choices=[category_type.value for category_type in CategoryType],
        help="Only show categories of one type.",
    )
    parser.add_argument("--category-id", help="Print details for one category.")
    parser.add_argument("--group-id", help="Print details for one category group.")
    parser.add_argument("--groups", action="store_true", help="Print category groups.")
    parser.add_argument("--catalog", action="store_true", help="Print ordered category catalog.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.category_id:
        category = get_category(session, args.category_id)
        if category is None:
            raise SystemExit("Category not found.")
        print_category(category)
        return

    if args.group_id:
        group = get_category_group(session, args.group_id)
        if group is None:
            raise SystemExit("Category group not found.")
        print_group(group)
        return

    if args.groups:
        groups = list_category_groups(session)
        print(f"Found {len(groups)} category groups.\n")
        print(f"{'Name':28} {'Type':10} {'Order':>5}")
        print("-" * 47)
        for group in groups:
            print(
                f"{clip(group.name, 28):28} "
                f"{category_type(group.type):10} "
                f"{format_int(group.order):>5}"
            )
        return

    if args.catalog:
        catalog = get_category_catalog(session, include_disabled=args.include_disabled)
        print(f"Found {len(catalog.groups)} groups and {len(catalog.categories)} categories.\n")
        print_catalog(catalog)
        return

    filters = CategoryFilter(types=[CategoryType(args.type)]) if args.type else None
    categories = list_categories(
        session,
        filters=filters,
        include_disabled=args.include_disabled,
    )

    print(f"Found {len(categories)} categories.\n")
    print(f"{'Name':30} {'Type':10} {'Group':26} {'Order':>5} {'Disabled':>8}")
    print("-" * 86)

    for category in categories:
        print(
            f"{clip(category.name, 30):30} "
            f"{category_type(category.type):10} "
            f"{clip(group_name(category), 26):26} "
            f"{format_int(category.order):>5} "
            f"{str(bool(category.is_disabled)):>8}"
        )


def print_category(category) -> None:
    print(f"Name: {category.icon or ''} {category.name}".strip())
    print(f"ID: {category.id}")
    print(f"Type: {category_type(category.type)}")
    print(f"Group: {group_name(category)}")
    print(f"Order: {format_int(category.order)}")
    print(f"System: {category.is_system}")
    print(f"Disabled: {category.is_disabled}")
    print(f"Protected: {category.is_protected}")
    print(f"Exclude from budget: {category.exclude_from_budget}")
    print(f"Budget variability: {category.budget_variability or ''}")


def print_group(group) -> None:
    print(f"Name: {group.name}")
    print(f"ID: {group.id}")
    print(f"Type: {category_type(group.type)}")
    print(f"Order: {format_int(group.order)}")
    print(f"Group-level budgeting: {group.group_level_budgeting_enabled}")
    print(f"Budget variability: {group.budget_variability or ''}")


def print_catalog(catalog) -> None:
    categories_by_group = {}
    for category in catalog.categories:
        group_id = category.group.id if category.group is not None else ""
        categories_by_group.setdefault(group_id, []).append(category)

    for group in catalog.groups:
        print(f"{group.name} ({category_type(group.type)})")
        for category in categories_by_group.get(group.id, []):
            disabled = " disabled" if category.is_disabled else ""
            print(f"  - {category.icon or ''} {category.name}{disabled}".strip())


def category_type(value) -> str:
    if value is None:
        return ""
    return value.value if isinstance(value, CategoryType) else str(value)


def group_name(category) -> str:
    if category.group is None:
        return ""
    return category.group.name or category.group.id


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
