# API Design Approach

This project is an unofficial Monarch Money API client. Its goal is to expose a practical, stable-feeling Python API for the things a user actually does in Monarch, not to mirror every backend endpoint discovered in network traffic.

## Core Philosophy

Build from user workflows, not backend routes.

Monarch's GraphQL and REST API is broad, sometimes unintuitive, and contains many operations that are only useful for internal UI wiring. We use recon data to learn what is possible, but we do not create a Python function just because a backend operation exists.

## Organization

Functions and types are organized by product group:

- `functions/auth.py`, `types/auth.py`
- `functions/accounts.py`, `types/accounts.py`
- future groups such as transactions, categories, merchants, budget, goals, tags, rules, household, etc.

Each group owns the concepts that naturally belong to that page or workflow in Monarch. If functionality overlaps, prefer a single clear owner and let other groups reference that object by id or by a shared type.

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
