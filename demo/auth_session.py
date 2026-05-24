from __future__ import annotations

from getpass import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import MfaRequiredError, create_session, load_session  # noqa: E402


def main() -> None:
    if SESSION_PATH.exists():
        session = load_session(SESSION_PATH)
        print(f"Loaded saved session for {session.email or session.user_id or 'unknown user'}.")
        return

    email = input("Monarch email: ").strip()
    password = getpass("Monarch password: ")

    try:
        session = create_session(email, password, session_path=SESSION_PATH)
    except MfaRequiredError:
        mfa_code = input("MFA code: ").strip()
        session = create_session(
            email,
            password,
            mfa_code=mfa_code,
            session_path=SESSION_PATH,
        )

    print(f"Created session for {session.email or session.user_id or 'unknown user'}.")
    print(f"Saved session to {SESSION_PATH}.")


if __name__ == "__main__":
    main()
