from __future__ import annotations

from argparse import ArgumentParser
from datetime import date
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    get_budget,
    get_budget_category,
    get_budget_settings,
    get_flex_rollover_settings,
    list_budget_months,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch budget data using demo/session.json.")
    parser.add_argument("--month", help="Budget month in YYYY-MM or YYYY-MM-DD format.")
    parser.add_argument("--start-month", help="Start month for a range.")
    parser.add_argument("--end-month", help="End month for a range.")
    parser.add_argument("--settings", action="store_true", help="Show budget settings.")
    parser.add_argument("--categories", action="store_true", help="Show category rows.")
    parser.add_argument("--groups", action="store_true", help="Show group rows.")
    parser.add_argument("--flex", action="store_true", help="Show flex budget row.")
    parser.add_argument("--rollover", action="store_true", help="Show flex rollover settings.")
    parser.add_argument("--category-id", help="Show one budget category row.")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.settings:
        print_settings(get_budget_settings(session))
        print()

    if args.rollover:
        print_flex_rollover(get_flex_rollover_settings(session))
        print()

    if args.category_id:
        month = args.month or current_month()
        row = get_budget_category(session, month, args.category_id)
        if row is None:
            raise SystemExit("Budget category not found.")
        print_category_rows([row])
        return

    if args.start_month or args.end_month:
        start_month = args.start_month or args.month or current_month()
        end_month = args.end_month or start_month
        budgets = list_budget_months(session, start_month, end_month)
        for budget in budgets:
            print_budget_summary(budget)
        return

    budget = get_budget(session, args.month or current_month())
    print_budget_summary(budget)

    show_default_rows = not (args.settings or args.groups or args.categories or args.flex)
    if args.flex or show_default_rows:
        print()
        print_flex(budget.flex)
    if args.groups:
        print()
        print_group_rows(budget.groups[: args.limit])
    if args.categories or show_default_rows:
        print()
        print_category_rows(budget.categories[: args.limit])


def print_settings(settings) -> None:
    print("Budget settings")
    print(f"  System: {enum_value(settings.budget_system)}")
    print(f"  Apply to future default: {format_bool(settings.apply_to_future_months_default)}")
    if settings.status is not None:
        print(f"  Has budget: {format_bool(settings.status.has_budget)}")
        print(f"  Has transactions: {format_bool(settings.status.has_transactions)}")


def print_flex_rollover(settings) -> None:
    print("Flex rollover settings")
    print(f"  System: {enum_value(settings.budget_system)}")
    rollover = settings.rollover_period
    if rollover is None:
        print("  Rollover: none")
        return
    print(f"  Start month: {rollover.start_month}")
    print(f"  Starting balance: {format_money(rollover.starting_balance)}")
    print(f"  Frequency: {rollover.frequency or ''}")


def print_budget_summary(budget) -> None:
    totals = budget.totals_by_month[0] if budget.totals_by_month else None
    print(f"Budget {budget.start_month[:7]}")
    print(f"  System: {enum_value(budget.budget_system)}")
    print(f"  Groups: {len(budget.groups)}")
    print(f"  Categories: {len(budget.categories)}")
    if budget.flex is not None and budget.flex.amount is not None:
        print(f"  Flex planned: {format_money(planned_value(budget.flex.amount))}")
    if totals is not None:
        print(f"  Income planned: {format_money(value(totals.income, 'planned_amount'))}")
        print(f"  Expenses planned: {format_money(value(totals.expenses, 'planned_amount'))}")
        print(f"  Expenses actual: {format_money(value(totals.expenses, 'actual_amount'))}")


def print_flex(flex) -> None:
    print("Flex")
    if flex is None or flex.amount is None:
        print("  No flex budget row.")
        return
    print(
        f"  {enum_value(flex.budget_variability):12} "
        f"{format_money(planned_value(flex.amount)):>12} "
        f"{format_money(flex.amount.actual_amount):>12} "
        f"{format_money(flex.amount.remaining_amount):>12}"
    )


def print_group_rows(rows) -> None:
    if not rows:
        return
    print(f"{'Group':32} {'Type':10} {'Variability':13} {'Planned':>12} {'Actual':>12}")
    print("-" * 84)
    for row in rows:
        amount = row.amount
        print(
            f"{clip(row.group.name or '', 32):32} "
            f"{enum_value(row.group.type):10} "
            f"{enum_value(row.group.budget_variability):13} "
            f"{format_money(planned_value(amount)):>12} "
            f"{format_money(amount.actual_amount if amount else None):>12}"
        )


def print_category_rows(rows) -> None:
    if not rows:
        return
    print(f"{'Category':32} {'Variability':13} {'Planned':>12} {'Actual':>12} {'Remaining':>12}")
    print("-" * 88)
    for row in rows:
        amount = row.amount
        print(
            f"{clip(row.category.name or row.category.id, 32):32} "
            f"{enum_value(row.category.budget_variability):13} "
            f"{format_money(planned_value(amount)):>12} "
            f"{format_money(amount.actual_amount if amount else None):>12} "
            f"{format_money(amount.remaining_amount if amount else None):>12}"
        )


def current_month() -> str:
    return date.today().replace(day=1).isoformat()


def planned_value(amount) -> float | None:
    if amount is None:
        return None
    return amount.planned_cash_flow_amount or amount.planned_amount


def value(obj, attr: str) -> float | None:
    if obj is None:
        return None
    return getattr(obj, attr)


def enum_value(value) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def clip(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return f"{value[: length - 1]}..."


if __name__ == "__main__":
    main()
