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
    set_budget_amount,
    set_budget_category_variability,
    set_budget_group_amount,
    set_budget_group_variability,
    set_flex_budget_amount,
)


def main() -> None:
    parser = ArgumentParser(description="Run live budget API checks.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Re-save current budget amounts without changing their values.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)
    month = date.today().replace(day=1).isoformat()

    settings = get_budget_settings(session)
    assert settings.budget_system is not None

    budget = get_budget(session, month)
    assert budget.budget_system is not None
    assert budget.totals_by_month
    assert budget.categories
    assert budget.groups

    months = list_budget_months(session, month, add_month(month))
    assert len(months) == 2

    category_row = first_budgeted_category(budget)
    fetched_category = get_budget_category(session, month, category_row.category.id)
    assert fetched_category is not None
    assert fetched_category.category.id == category_row.category.id

    flex_settings = get_flex_rollover_settings(session)
    assert flex_settings.budget_system is not None

    if args.write:
        run_noop_write_checks(session, month, budget, category_row)

    print("Budget live test passed.")


def run_noop_write_checks(session, month: str, budget, category_row) -> None:
    category_amount = current_amount(category_row.amount)
    updated_category = set_budget_amount(
        session,
        month,
        category_row.category.id,
        category_amount,
        apply_to_future=False,
    )
    assert current_amount(updated_category.amount) == category_amount

    if category_row.category.budget_variability is not None:
        category = set_budget_category_variability(
            session,
            category_row.category.id,
            category_row.category.budget_variability,
        )
        assert category.budget_variability == category_row.category.budget_variability

    group_row = first_writable_group(budget)
    if group_row is not None:
        group_amount = current_amount(group_row.amount)
        updated_group = set_budget_group_amount(
            session,
            month,
            group_row.group.id,
            group_amount,
            apply_to_future=False,
        )
        assert current_amount(updated_group.amount) == group_amount

    variability_group = first_group_with_variability(budget)
    if variability_group is not None:
        group = set_budget_group_variability(
            session,
            variability_group.group.id,
            variability_group.group.budget_variability,
        )
        assert group.budget_variability == variability_group.group.budget_variability

    if budget.flex is not None and budget.flex.amount is not None:
        flex_amount = current_amount(budget.flex.amount)
        updated_flex = set_flex_budget_amount(
            session,
            month,
            flex_amount,
            apply_to_future=False,
        )
        assert current_amount(updated_flex.amount) == flex_amount


def first_budgeted_category(budget):
    for row in budget.categories:
        if row.category.exclude_from_budget:
            continue
        if row.amount is not None:
            return row
    raise SystemExit("No budgeted category row available for budget tests.")


def first_writable_group(budget):
    for row in budget.groups:
        if row.group.group_level_budgeting_enabled and row.amount is not None:
            return row
    return None


def first_group_with_variability(budget):
    for row in budget.groups:
        if row.group.budget_variability is not None:
            return row
    return None


def current_amount(amount) -> float:
    if amount is None:
        return 0.0
    value = amount.planned_cash_flow_amount
    if value is None:
        value = amount.planned_amount
    return value or 0.0


def add_month(month: str) -> str:
    value = date.fromisoformat(month)
    year = value.year + (1 if value.month == 12 else 0)
    next_month = 1 if value.month == 12 else value.month + 1
    return date(year, next_month, 1).isoformat()


if __name__ == "__main__":
    main()
