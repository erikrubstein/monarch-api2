# API Design Approach

This project is an unofficial Monarch Money API client. Its goal is to expose a practical, stable-feeling Python API for the things a user actually does in Monarch, not to mirror every backend endpoint discovered in network traffic.

## Core Philosophy

Build from user workflows, not backend routes.

Monarch's GraphQL and REST API is broad, sometimes unintuitive, and contains many operations that are only useful for internal UI wiring. We use recon data to learn what is possible, but we do not create a Python function just because a backend operation exists.

## Organization

Functions and types are organized by product group:

- `functions/auth.py`, `types/auth.py`
- `functions/accounts.py`, `types/accounts.py`
- `functions/categories.py`, `types/categories.py`
- `functions/tags.py`, `types/tags.py`
- `functions/merchants.py`, `types/merchants.py`
- `functions/transactions.py`, `types/transactions.py`
- `functions/cashflow.py`, `types/cashflow.py`
- `functions/reports.py`, `types/reports.py`
- `functions/recurring.py`, `types/recurring.py`
- `functions/household.py`, `types/household.py`
- `functions/goals.py`, `types/goals.py`
- future groups such as budget, receipts, investments, rules, etc.

Each group owns the concepts that naturally belong to that page or workflow in Monarch. If functionality overlaps, prefer a single clear owner and let other groups reference that object by id or by a shared type.

## Group Workflow

Build the API one product group at a time. Do not start by implementing every endpoint discovered in recon.

For each group, use this workflow:

1. Plan the group from the Monarch web app page or workflow.
2. Decide which user-facing capabilities are fundamental and which should be deferred.
3. Define ownership boundaries with neighboring groups so functionality is not duplicated.
4. Identify the backend operations in `recon/` that support those capabilities.
5. Design the public functions and types before writing implementation code.
6. Refine names so they make sense in this API, even when Monarch's backend uses different names.
7. Implement the smallest useful public surface.
8. Run live read-only tests first when possible, then narrow write tests when the group includes mutations.
9. Create or update ignored demo scripts in `demo/` that show normal usage through `demo/session.json`.
10. Update docs with any design decisions, deferred behavior, or backend quirks discovered during implementation.
11. Commit the group only after the implementation, docs, live tests, and demos are in a coherent state.

The plan/refine step matters. It is acceptable, and expected, to rename functions, collapse types, or defer behavior before committing a group.

## Implementation Checklist

Each completed group should usually include:

- one file in `src/monarch_api/functions/`
- one file in `src/monarch_api/types/`
- public exports in `src/monarch_api/functions/__init__.py`
- public exports in `src/monarch_api/types/__init__.py`
- public exports in `src/monarch_api/__init__.py`
- documentation updates in `API_DESIGN.md` or `MONARCH_API_FUNCTION_PLAN.md`
- an ignored demo script in `demo/` when the group has useful live behavior to show

Before committing a group, run at least:

```powershell
python -m compileall src demo
git status --short
```

Also run live Monarch calls using `demo/session.json` whenever the function can be safely tested. Prefer read-only live tests for list/detail/summary functions. For mutations, use narrow temporary records where possible and clean them up in the same test.

## Function Rules

Add a function when it represents a meaningful user-facing capability.

Good examples:

- `list_accounts`
- `get_account`
- `get_account_history`
- `get_net_worth_performance`
- `get_net_worth_breakdown`
- `create_manual_account`

Avoid functions that only exist because Monarch has an endpoint. UI-only support queries, provider-specific flows, narrowly internal mutations, and rarely used backend operations should be deferred unless they become necessary for a real workflow.

Prefer functions that are broad enough to be useful but still conceptually clear. A filter argument is usually better than many small functions for every sort, search, or filter variation.

## Naming Rules

Public names should make sense to a Python user, even when they do not match Monarch's GraphQL names.

Examples:

- GraphQL `displayBalance` maps to public `balance`.
- GraphQL `signedBalance` maps to public `balance`.
- GraphQL `aggregateSnapshots` is exposed as `get_net_worth_performance`.
- GraphQL `snapshotsByAccountType` is exposed as `get_net_worth_breakdown`.
- GraphQL `deleteCategory` is exposed as `remove_category` because system categories are deactivated rather than truly deleted.

GraphQL names may remain inside private query strings and mapping code, but they should not leak into public function names, type names, or field names unless the backend term is also the clearest user-facing term.

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

Avoid one-function input types unless there is a strong reason. If an input type is only used by one function, flatten it into keyword arguments.

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

Use `raw` sparingly on backend-backed return types when preserving the original Monarch response is useful. Do not add `raw` to input/helper types or client-created convenience containers.

## Endpoint Usage

Backend endpoint names and GraphQL operation names are implementation details. A public function may use one endpoint, several endpoints, or a subset of one endpoint.

When implementing a function:

1. Start from the user-facing behavior.
2. Use recon data to find the smallest reliable backend operation that supports it.
3. Select only the fields needed for the public type.
4. Map backend field names to clear public names.
5. Keep the function in the group that owns the concept.

## Scope Control

When in doubt, leave functionality out until it is clearly useful.

It is easier to add a well-named function later than to remove or rename a function that should never have been public. This API should stay small, boring, and obvious.
