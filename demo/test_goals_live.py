from __future__ import annotations

from datetime import date
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    GoalType,
    archive_goal,
    contribute_to_goal,
    create_goal,
    create_transaction,
    delete_goal,
    delete_goal_event,
    delete_transaction,
    get_goal_budget_amounts,
    graphql_request,
    link_goal_account_balance,
    list_categories,
    list_goal_events,
    load_session,
    restore_goal,
    set_goal_budget_amount,
    unlink_goal_account,
    update_goal,
    update_goal_event,
    update_transaction,
)


def main() -> None:
    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)
    goal = None
    transaction = None
    event_id = None
    linked_account_id = None

    try:
        account = first_asset_account(session)
        category = next(
            (category for category in list_categories(session) if not category.exclude_from_budget),
            None,
        )
        if category is None:
            raise SystemExit("No budgeted category available for transaction test.")

        goal = create_goal(
            session,
            name="Codex API SavingsGoal Live Test",
            goal_type=GoalType.CUSTOM,
            target_amount=123.45,
            planned_monthly_contribution=10.0,
            is_sinking_fund=True,
        )
        assert goal.name == "Codex API SavingsGoal Live Test"

        goal = update_goal(
            session,
            goal.id,
            name="Codex API SavingsGoal Live Updated",
            target_amount=234.56,
            planned_monthly_contribution=11.0,
        )
        assert goal.name == "Codex API SavingsGoal Live Updated"
        assert goal.target_amount == 234.56

        month = date.today().replace(day=1).isoformat()
        assert set_goal_budget_amount(session, goal.id, month, 9.99)
        budget_amounts = get_goal_budget_amounts(session, goal.id, month, month)
        assert budget_amounts and budget_amounts[0].planned_amount == 9.99

        if not account.get("linkedGoal"):
            linked_account_id = str(account["id"])
            goal = link_goal_account_balance(
                session,
                goal.id,
                linked_account_id,
                use_entire_balance=True,
            )
            assert any(
                link.account is not None
                and link.account.id == linked_account_id
                and link.use_entire_balance
                for link in goal.account_balance_links
            )
            goal = unlink_goal_account(session, goal.id, linked_account_id)
            assert not any(
                link.account is not None and link.account.id == linked_account_id
                for link in goal.account_balance_links
            )
            linked_account_id = None

        event = contribute_to_goal(
            session,
            goal.id,
            str(account["id"]),
            amount=1.23,
            date=date.today().isoformat(),
            include_in_budget=False,
            notes="Temporary live goal test",
        )
        event_id = event.id
        assert event.amount == 1.23
        event = update_goal_event(
            session,
            event.id,
            date=date.today().isoformat(),
            notes="Temporary live goal test updated",
        )
        assert event.notes == "Temporary live goal test updated"
        assert delete_goal_event(session, event.id)
        event_id = None
        assert not list_goal_events(session, goal.id)

        goal = archive_goal(session, goal.id)
        assert goal.archived_at is not None
        goal = restore_goal(session, goal.id)
        assert goal.archived_at is None

        transaction = create_transaction(
            session,
            account_id=str(account["id"]),
            amount=-0.77,
            date=date.today().isoformat(),
            merchant_name="Codex API SavingsGoal Live Tx",
            category_id=category.id,
            notes="Temporary live savings-goal transaction test",
            should_update_balance=False,
        )
        transaction = update_transaction(session, transaction.id, goal_id=goal.id)
        assert transaction.goal is not None and transaction.goal.id == goal.id
        transaction = update_transaction(session, transaction.id, clear_goal=True)
        assert transaction.goal is None

        print("Goals live test passed.")
    finally:
        if event_id is not None:
            delete_goal_event(session, event_id)
        if transaction is not None:
            delete_transaction(session, transaction.id)
        if linked_account_id is not None and goal is not None:
            unlink_goal_account(session, goal.id, linked_account_id)
        if goal is not None:
            delete_goal(session, goal.id)


def first_asset_account(session):
    data = graphql_request(
        session,
        "GoalLiveTestAccounts",
        """
query GoalLiveTestAccounts {
  accounts(filters: { includeHidden: false }) {
    id
    displayName
    isAsset
    linkedGoal {
      id
      name
    }
  }
}
""",
    )
    accounts = [
        account
        for account in data.get("accounts") or []
        if isinstance(account, dict) and account.get("isAsset")
    ]
    if not accounts:
        raise SystemExit("No visible asset account available for goal tests.")
    return next((account for account in accounts if not account.get("linkedGoal")), accounts[0])


if __name__ == "__main__":
    main()
