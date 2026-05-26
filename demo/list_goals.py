from __future__ import annotations

import sys
from argparse import ArgumentParser
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    get_goal,
    get_goal_budget_amounts,
    list_goal_events,
    list_goals,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch savings goals using demo/session.json.")
    parser.add_argument("--goal-id", help="Print details for one goal.")
    parser.add_argument("--events", action="store_true", help="Show events for --goal-id.")
    parser.add_argument("--budget", action="store_true", help="Show budget amounts for --goal-id.")
    parser.add_argument("--start-month", help="Budget start month in YYYY-MM-DD format.")
    parser.add_argument("--end-month", help="Budget end month in YYYY-MM-DD format.")
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.goal_id:
        goal = get_goal(session, args.goal_id)
        if goal is None:
            raise SystemExit("Goal not found.")
        print_goal(goal)

        if args.events:
            events = list_goal_events(session, args.goal_id)
            print(f"\nEvents: {len(events)}")
            print_events(events[: args.limit])

        if args.budget:
            start_month, end_month = month_range(args.start_month, args.end_month)
            amounts = get_goal_budget_amounts(
                session,
                args.goal_id,
                start_month,
                end_month,
            )
            print(f"\nBudget amounts from {start_month} to {end_month}: {len(amounts)}")
            print_budget_amounts(amounts)
        return

    goals = list_goals(session, include_archived=args.include_archived)
    print(f"Found {len(goals)} goals.\n")
    print(f"{'Name':32} {'Status':12} {'Current':>12} {'Target':>12} {'Progress':>9}")
    print("-" * 83)
    for goal in goals[: args.limit]:
        print(
            f"{clip(goal.name, 32):32} "
            f"{status(goal):12} "
            f"{format_money(goal.current_balance):>12} "
            f"{format_money(goal.target_amount):>12} "
            f"{format_percent(goal.progress):>9}"
        )


def print_goal(goal) -> None:
    print(f"ID: {goal.id}")
    print(f"Name: {goal.name}")
    print(f"Type: {goal.type.value if goal.type else ''}")
    print(f"Status: {status(goal)}")
    print(f"Current balance: {format_money(goal.current_balance)}")
    print(f"Target amount: {format_money(goal.target_amount)}")
    print(f"Target date: {goal.target_date or ''}")
    print(f"Progress: {format_percent(goal.progress)}")
    print(f"Monthly planned contribution: {format_money(goal.current_month_planned_contribution_amount)}")
    print(f"Archived at: {goal.archived_at or ''}")
    print(f"Completed at: {goal.completed_at or ''}")
    print(f"Account balance links: {len(goal.account_balance_links)}")
    for link in goal.account_balance_links:
        print(
            f"  {account_name(link.account)}: "
            f"{format_money(link.current_amount)} "
            f"(entire balance: {format_bool(link.use_entire_balance)})"
        )


def print_events(events) -> None:
    if not events:
        return
    print(f"{'Date':10} {'Amount':>12} {'Type':24} {'Account':24} {'Budget':>6}")
    print("-" * 82)
    for event in events:
        print(
            f"{event.date[:10]:10} "
            f"{format_money(event.amount):>12} "
            f"{event_type(event):24} "
            f"{clip(account_name(event.account), 24):24} "
            f"{format_bool(event.include_in_budget):>6}"
        )


def print_budget_amounts(amounts) -> None:
    if not amounts:
        return
    print(f"{'Month':10} {'Planned':>12} {'Actual':>12} {'Remaining':>12}")
    print("-" * 52)
    for amount in amounts:
        print(
            f"{amount.month[:10]:10} "
            f"{format_money(amount.planned_amount):>12} "
            f"{format_money(amount.actual_amount):>12} "
            f"{format_money(amount.remaining_amount):>12}"
        )


def month_range(start_month: str | None, end_month: str | None) -> tuple[str, str]:
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    return start_month or month_start, end_month or month_start


def status(goal) -> str:
    if goal.status is None:
        return ""
    return goal.status.value


def event_type(event) -> str:
    if event.type is None:
        return ""
    return event.type.value


def account_name(account) -> str:
    if account is None:
        return ""
    return account.display_name


def format_money(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.0f}%"


def format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
