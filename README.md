# monarch-api2

Unofficial Python client for Monarch Money. It provides a practical,
user-workflow-oriented API for accounts, transactions, receipts, budgets, goals,
recurring activity, reports, cashflow, investments, categories, merchants, tags,
and household settings.

The public API is intentionally not a one-to-one mirror of every Monarch backend
operation. It uses network traffic and webapp behavior to understand what the
backend can do, then exposes Python functions around the tasks a caller is
likely trying to accomplish.

It is not affiliated with Monarch Money.

## Design Approach

The API is built by product area, not by backend endpoint:

- Functions live in `src/monarch_api/functions/`.
- Structured return types live in `src/monarch_api/types/`.
- Public exports are available from `monarch_api`.

Each group owns a clear workflow. Transactions own transaction edits and
attachments. Receipts own scanned receipts. Goals own goal records and goal
events. Budget owns monthly budget rows and rollover settings. Neighboring
groups reference shared concepts by id rather than duplicating behavior.

Some Monarch features are intentionally omitted for now:

- Rules and automation setup.
- Risky bulk/destructive workflows without a clear day-to-day need.
- Provider-specific account connection flows.
- Invitation, subscription, advisor, security, and other account-admin edges.
- Raw recon artifacts and captured network traffic.

## Installation

This project targets Python 3.11+.

From a local checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

From GitHub:

```bash
pip install "git+https://github.com/erikrubstein/monarch-api2.git"
```

## Getting Started

Create and save an authenticated session:

```python
from monarch_api import create_session

session = create_session(
    "you@example.com",
    "your-password",
    session_path="session.json",
)
```

If MFA is required:

```python
from monarch_api import create_session

session = create_session(
    "you@example.com",
    "your-password",
    mfa_code="123456",
    session_path="session.json",
)
```

Load an existing session and call the API:

```python
from monarch_api import load_session, list_accounts, list_transactions

session = load_session("session.json")

accounts = list_accounts(session)
transactions = list_transactions(session, limit=25)
```

Example receipt upload:

```python
from pathlib import Path

from monarch_api import load_session, upload_receipt, get_receipt

session = load_session("session.json")
receipt = upload_receipt(session, Path.home() / "Downloads" / "receipt.png")

# Monarch scans receipts asynchronously. The first result may be in_progress.
parsed = get_receipt(session, receipt.id)
```

## Function Overview

All authenticated functions take `session` as their first argument.

### Auth

- `create_session`
- `save_session`
- `load_session`

### Accounts

- `list_accounts`
- `get_account`
- `get_net_worth_performance`
- `get_net_worth_breakdown`
- `get_historical_balances`
- `get_account_history`
- `create_manual_account`
- `update_account`
- `delete_account`

### Transactions

- `list_transactions`
- `get_transaction`
- `create_transaction`
- `update_transaction`
- `delete_transaction`
- `get_transaction_splits`
- `update_transaction_splits`
- `unsplit_transaction`
- `list_transaction_attachments`
- `get_transaction_attachment`
- `upload_transaction_attachment`
- `download_transaction_attachment`
- `delete_transaction_attachment`

### Receipts

- `list_receipts`
- `get_receipt`
- `upload_receipt`
- `delete_receipt`
- `match_receipt`
- `unmatch_receipt`
- `update_receipt`
- `get_receipt_settings`
- `update_receipt_settings`

### Cashflow

- `get_cashflow_summary`
- `get_cashflow_trends`
- `get_cashflow_breakdown`

### Reports

- `get_report_data`
- `list_saved_reports`
- `get_saved_report`
- `create_saved_report`
- `update_saved_report`
- `delete_saved_report`

### Budget

- `get_budget`
- `list_budget_months`
- `get_budget_settings`
- `get_budget_category`
- `get_flex_rollover_settings`
- `set_budget_amount`
- `set_budget_group_amount`
- `set_flex_budget_amount`
- `set_budget_category_variability`
- `set_budget_group_variability`
- `set_budget_category_rollover`
- `set_budget_group_rollover`
- `set_flex_rollover_settings`
- `reset_budget_rollover`
- `create_budget`
- `reset_budget`
- `clear_budget`

### Recurring

- `list_recurring_streams`
- `get_recurring_stream`
- `list_recurring_occurrences`
- `get_recurring_summary`
- `create_recurring_stream`
- `update_recurring_stream`
- `remove_recurring_stream`

### Goals

- `list_goals`
- `get_goal`
- `create_goal`
- `update_goal`
- `delete_goal`
- `archive_goal`
- `restore_goal`
- `update_goal_priorities`
- `link_goal_account_balance`
- `unlink_goal_account`
- `list_goal_events`
- `contribute_to_goal`
- `withdraw_from_goal`
- `update_goal_event`
- `delete_goal_event`
- `get_goal_budget_amounts`
- `set_goal_budget_amount`

### Investments

- `list_investment_accounts`
- `get_portfolio`
- `list_holdings`
- `get_holding`
- `search_securities`
- `get_security`
- `get_holding_performance`
- `create_manual_holding`
- `update_manual_holding`
- `delete_manual_holding`

### Categories

- `list_categories`
- `list_category_groups`
- `get_category_catalog`
- `get_category`
- `get_category_group`
- `create_category`
- `update_category`
- `remove_category`
- `reactivate_category`
- `reorder_category`
- `create_category_group`
- `update_category_group`
- `delete_category_group`
- `reorder_category_group`

### Merchants

- `list_merchants`
- `get_merchant`
- `update_merchant`
- `delete_merchant`

### Tags

- `list_tags`
- `get_tag`
- `create_tag`
- `update_tag`
- `delete_tag`
- `reorder_tag`

### Household

- `get_household`
- `list_household_members`
- `get_household_member`
- `get_current_user`
- `update_current_user`
- `get_household_preferences`
- `update_household_preferences`

## Safety Notes

This is an unofficial client for private backend APIs. Monarch may change
operation names, fields, authentication behavior, or validation rules without
notice.
