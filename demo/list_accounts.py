from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    AccountFilter,
    get_account,
    get_account_history,
    get_net_worth_performance,
    list_accounts,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(description="Show Monarch account data using demo/session.json.")
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--account-id", help="Print details for one account.")
    parser.add_argument("--account-history", help="Print balance history for one account.")
    parser.add_argument("--net-worth", action="store_true", help="Print recent net worth performance.")
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)
    if args.account_history:
        history = get_account_history(session, args.account_history)
        for point in history[-12:]:
            print(f"{point.date}: {format_balance(point.balance)}")
        return

    if args.account_id:
        account = get_account(session, args.account_id)
        if account is None:
            raise SystemExit("Account not found.")
        print_account(account)
        return

    if args.net_worth:
        snapshots = get_net_worth_performance(session)
        for snapshot in snapshots[-12:]:
            print(
                f"{snapshot.date}: "
                f"net={format_balance(snapshot.net_worth)} "
                f"assets={format_balance(snapshot.assets_balance)} "
                f"liabilities={format_balance(snapshot.liabilities_balance)}"
            )
        return

    filters = AccountFilter(include_hidden=True) if args.include_hidden else None
    accounts = list_accounts(session, filters=filters)

    print(f"Found {len(accounts)} accounts.\n")
    print(f"{'Name':36} {'Type':18} {'Institution':24} {'Balance':>14}")
    print("-" * 95)

    for account in accounts:
        print(
            f"{clip(account.display_name, 36):36} "
            f"{clip(account_type(account), 18):18} "
            f"{clip(institution_name(account), 24):24} "
            f"{format_balance(account.balance):>14}"
        )


def print_account(account) -> None:
    print(f"Name: {account.display_name}")
    print(f"ID: {account.id}")
    print(f"Type: {account_type(account)}")
    print(f"Institution: {institution_name(account)}")
    print(f"Balance: {format_balance(account.balance)}")
    print(f"Current balance: {format_balance(account.current_balance)}")
    print(f"Last updated: {account.last_updated_at or ''}")
    print(f"Owner: {owner_name(account)}")
    print(f"Manual: {account.is_manual}")
    print(f"Hidden: {account.is_hidden}")
    print(f"Included in net worth: {account.include_in_net_worth}")


def account_type(account) -> str:
    if account.subtype and account.subtype.display_name:
        return account.subtype.display_name
    if account.type and account.type.display_name:
        return account.type.display_name
    return ""


def institution_name(account) -> str:
    if account.institution and account.institution.name:
        return account.institution.name
    return "Manual" if account.is_manual else ""


def owner_name(account) -> str:
    if account.owner is None:
        return "Shared"
    return account.owner.display_name or account.owner.id


def format_balance(balance: float | None) -> str:
    if balance is None:
        return ""
    return f"${balance:,.2f}"


def clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


if __name__ == "__main__":
    main()
