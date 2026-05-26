from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import (  # noqa: E402
    get_current_user,
    get_household,
    get_household_member,
    get_household_preferences,
    list_household_members,
    load_session,
)


def main() -> None:
    parser = ArgumentParser(
        description="Show Monarch household data using demo/session.json."
    )
    parser.add_argument("--member-id", help="Print details for one household member.")
    parser.add_argument("--user", action="store_true", help="Print current user details.")
    parser.add_argument(
        "--preferences",
        action="store_true",
        help="Print household preferences.",
    )
    args = parser.parse_args()

    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)

    if args.user:
        print_user(get_current_user(session))
        return

    if args.preferences:
        print_preferences(get_household_preferences(session))
        return

    if args.member_id:
        member = get_household_member(session, args.member_id)
        if member is None:
            raise SystemExit("Household member not found.")
        print_member(member)
        return

    household = get_household(session)
    members = list_household_members(session)

    print(f"Household: {household.name or ''}")
    print(f"ID: {household.id}")
    print(f"Location: {format_location(household)}")
    print(f"\nFound {len(members)} household members.\n")
    print(f"{'Name':28} {'Email':34} {'Role':16} {'MFA':>5}")
    print("-" * 87)
    for member in members:
        print(
            f"{clip(member.display_name or member.name or '', 28):28} "
            f"{clip(member.email or '', 34):34} "
            f"{format_role(member.role):16} "
            f"{format_bool(member.has_mfa_on):>5}"
        )


def print_member(member) -> None:
    print(f"Name: {member.display_name or member.name or ''}")
    print(f"ID: {member.id}")
    print(f"Email: {member.email or ''}")
    print(f"Role: {format_role(member.role)}")
    print(f"MFA: {format_bool(member.has_mfa_on)}")
    print(f"Profile picture: {member.profile_picture_url or ''}")


def print_user(user) -> None:
    print(f"Name: {user.display_name or user.name or ''}")
    print(f"ID: {user.id}")
    print(f"Email: {user.email or ''}")
    print(f"Timezone: {user.timezone or ''}")
    print(f"Role: {format_role(user.household_role)}")
    print(f"Password: {format_bool(user.has_password)}")
    print(f"MFA: {format_bool(user.has_mfa_on)}")
    print(f"Created: {user.created_at or ''}")


def print_preferences(preferences) -> None:
    print(f"ID: {preferences.id}")
    print(f"Budget system: {preferences.budget_system or ''}")
    print(
        "New transactions need review: "
        f"{format_bool(preferences.new_transactions_need_review)}"
    )
    print(
        "Uncategorized transactions need review: "
        f"{format_bool(preferences.uncategorized_transactions_need_review)}"
    )
    print(
        "Pending transactions can be edited: "
        f"{format_bool(preferences.pending_transactions_can_be_edited)}"
    )
    print(
        "Hidden transactions beta: "
        f"{format_bool(preferences.hidden_transactions_beta_enabled)}"
    )
    print(
        "Exclude business from budget: "
        f"{format_bool(preferences.exclude_business_from_budget)}"
    )


def format_location(household) -> str:
    parts = [
        household.city,
        household.state,
        household.zip_code,
        household.country,
    ]
    return ", ".join(part for part in parts if part)


def format_role(role) -> str:
    if role is None:
        return ""
    if hasattr(role, "value"):
        return str(role.value)
    return str(role)


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
