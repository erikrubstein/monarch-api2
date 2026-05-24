from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
SESSION_PATH = PROJECT_ROOT / "demo" / "session.json"

sys.path.insert(0, str(SRC_ROOT))

from monarch_api import graphql_request, load_session  # noqa: E402

QUERY = """
query Common_GetMe {
  me {
    id
    email
    displayName
  }
}
"""


def main() -> None:
    if not SESSION_PATH.exists():
        raise SystemExit("Run demo/auth_session.py first to create demo/session.json.")

    session = load_session(SESSION_PATH)
    data = graphql_request(session, "Common_GetMe", QUERY)
    me = data["me"]

    display_name = me.get("displayName") or me.get("email") or me["id"]
    print(f"Session is valid for {display_name}.")


if __name__ == "__main__":
    main()
