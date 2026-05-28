# Agent Instructions

This repository is an unofficial Monarch Money API client. Build it as a
practical, stable-feeling Python API for the things a user actually does in
Monarch, not as a one-to-one mirror of every backend endpoint.

## Core Philosophy

Build from user workflows, not backend routes.

Monarch's GraphQL and REST API is broad, sometimes unintuitive, and includes
operations that are only useful for internal UI wiring. Backend behavior can be
used to learn what is possible, but do not create a public Python function just
because a backend operation exists.

Prefer a small, clear, user-facing API over a complete dump of backend
capabilities.

## Organization

Functions and types are organized by product group:

- `src/monarch_api/functions/auth.py`, `src/monarch_api/types/auth.py`
- `src/monarch_api/functions/accounts.py`, `src/monarch_api/types/accounts.py`
- `src/monarch_api/functions/transactions.py`, `src/monarch_api/types/transactions.py`
- `src/monarch_api/functions/receipts.py`, `src/monarch_api/types/receipts.py`
- `src/monarch_api/functions/cashflow.py`, `src/monarch_api/types/cashflow.py`
- `src/monarch_api/functions/reports.py`, `src/monarch_api/types/reports.py`
- `src/monarch_api/functions/budget.py`, `src/monarch_api/types/budget.py`
- `src/monarch_api/functions/recurring.py`, `src/monarch_api/types/recurring.py`
- `src/monarch_api/functions/goals.py`, `src/monarch_api/types/goals.py`
- `src/monarch_api/functions/investments.py`, `src/monarch_api/types/investments.py`
- `src/monarch_api/functions/categories.py`, `src/monarch_api/types/categories.py`
- `src/monarch_api/functions/merchants.py`, `src/monarch_api/types/merchants.py`
- `src/monarch_api/functions/tags.py`, `src/monarch_api/types/tags.py`
- `src/monarch_api/functions/household.py`, `src/monarch_api/types/household.py`

Each group owns the concepts that naturally belong to that Monarch page or
workflow. If functionality overlaps, prefer a single clear owner and let other
groups reference that object by id or by a shared type.

## Implementation Workflow

When adding or changing an API group:

1. Start from the Monarch web app workflow or user task.
2. Decide which capabilities are fundamental and which should be deferred.
3. Define ownership boundaries with neighboring groups.
4. Identify the backend operation or operations that support the behavior.
5. Design public functions and types before writing implementation code.
6. Refine names so they make sense in this Python API, even when Monarch's
   backend uses different names.
7. Implement the smallest useful public surface.
8. Run safe read-only tests first when possible, then narrow write tests when
   the group includes mutations.
9. Update `README.md` if the public surface or project guidance changes.
10. Commit only after implementation, exports, docs, and verification are
    coherent.

The plan/refine step matters. It is acceptable and expected to rename functions,
collapse types, or defer behavior before committing a public API.

## Implementation Checklist

Most completed groups should include:

- one file in `src/monarch_api/functions/`
- one file in `src/monarch_api/types/`
- public exports in `src/monarch_api/functions/__init__.py`
- public exports in `src/monarch_api/types/__init__.py`
- public exports in `src/monarch_api/__init__.py`
- focused tests or live verification when safe
- README updates when user-facing behavior changes

Before committing, run at least:

```bash
python -m compileall -q src
git diff --check
git status --short
```

Run live Monarch calls only when they are necessary and safe. Prefer read-only
live checks for list/detail/summary functions. For mutations, use narrow test
records where possible and clean them up in the same pass.

Do not commit credentials, session files, cookies, screenshots containing
private data, or captured network traffic.

## Function Rules

Add a function when it represents a meaningful user-facing capability.

Good examples:

- `list_accounts`
- `get_account`
- `get_account_history`
- `get_net_worth_performance`
- `get_net_worth_breakdown`
- `create_manual_account`

Avoid functions that only exist because Monarch has an endpoint. UI-only support
queries, provider-specific flows, narrowly internal mutations, and rarely used
backend operations should be deferred unless they become necessary for a real
workflow.

Prefer functions that are broad enough to be useful but still conceptually
clear. A filter argument is usually better than many small functions for every
sort, search, or filter variation.

## Naming Rules

Public names should make sense to a Python user, even when they do not match
Monarch's GraphQL names.

Examples:

- GraphQL `displayBalance` maps to public `balance`.
- GraphQL `signedBalance` maps to public `balance`.
- GraphQL `aggregateSnapshots` is exposed as `get_net_worth_performance`.
- GraphQL `snapshotsByAccountType` is exposed as `get_net_worth_breakdown`.
- GraphQL `deleteCategory` is exposed as `remove_category` because system
  categories are deactivated rather than truly deleted.

GraphQL names may remain inside private query strings and mapping code, but
they should not leak into public function names, type names, or field names
unless the backend term is also the clearest user-facing term.

## Type Rules

Types should mostly represent shared domain objects or structured return values.

Good shared/domain types:

- `AuthSession`
- `Account`
- `AccountType`
- `CategoryType`
- `Institution`
- `AccountFilter`
- `Tag`
- `Merchant`

Good return types:

- `AccountBalance`
- `AccountHistoryPoint`
- `NetWorthSnapshot`
- `NetWorthBreakdownPoint`

Avoid one-function input types unless there is a strong reason. If an input type
is only used by one function, flatten it into keyword arguments.

Prefer:

```python
create_manual_account(
    session,
    name="Cash",
    type="cash",
    subtype="cash",
    balance=100,
    owner_user_id=user_id,
)
```

Instead of:

```python
create_manual_account(session, ManualAccountCreate(...))
```

Use `raw` sparingly on backend-backed return types when preserving the original
Monarch response is useful. Do not add `raw` to input/helper types or
client-created convenience containers.

## Endpoint Usage

Backend endpoint names and GraphQL operation names are implementation details.
A public function may use one endpoint, several endpoints, or a subset of one
endpoint.

When implementing a function:

1. Start from the user-facing behavior.
2. Use the smallest reliable backend operation that supports it.
3. Select only the fields needed for the public type.
4. Map backend field names to clear public names.
5. Keep the function in the group that owns the concept.

## Scope Control

When in doubt, leave functionality out until it is clearly useful.

It is easier to add a well-named function later than to remove or rename a
function that should never have been public. This API should stay small,
boring, and obvious.
