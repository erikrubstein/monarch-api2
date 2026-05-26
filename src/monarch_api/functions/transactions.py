from __future__ import annotations

from collections.abc import Sequence

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    Transaction,
    TransactionFilter,
    TransactionPage,
    TransactionReviewStatus,
    TransactionSplit,
    TransactionSplitDetails,
    TransactionSplitDraft,
    TransactionSort,
)


TRANSACTION_USER_FIELDS = """
fragment TransactionUserFields on User {
  id
  displayName
  profilePictureUrl
}
"""

TRANSACTION_FIELDS = (
    """
fragment TransactionFields on Transaction {
  id
  amount
  pending
  date
  originalDate
  hideFromReports
  hiddenByAccount
  plaidName
  notes
  isRecurring
  reviewStatus
  needsReview
  reviewedAt
  isSplitTransaction
  hasSplitTransactions
  isManual
  dataProviderDescription
  deletedAt
  updatedAt
  attachments {
    id
  }
  goal {
    id
    name
  }
  savingsGoalEvent {
    id
    goal {
      id
      name
    }
  }
  category {
    id
    name
    icon
    group {
      id
      type
    }
  }
  merchant {
    id
    name
    logoUrl
    transactionCount
    transactionsCount
    recurringTransactionStream {
      id
    }
  }
  tags {
    id
    name
    color
    order
  }
  account {
    id
    displayName
    icon
    logoUrl
  }
  originalTransaction {
    id
  }
  ownedByUser {
    ...TransactionUserFields
  }
  reviewedByUser {
    ...TransactionUserFields
  }
  needsReviewByUser {
    ...TransactionUserFields
  }
}
"""
    + TRANSACTION_USER_FIELDS
)

TRANSACTION_SPLIT_FIELDS = (
    """
fragment TransactionSplitFields on Transaction {
  id
  amount
  date
  notes
  hideFromReports
  reviewStatus
  needsReview
  merchant {
    id
    name
    logoUrl
    transactionCount
    transactionsCount
    recurringTransactionStream {
      id
    }
  }
  category {
    id
    icon
    name
    group {
      id
      type
    }
  }
  goal {
    id
    name
  }
  savingsGoalEvent {
    id
    goal {
      id
      name
    }
    account {
      id
    }
  }
  needsReviewByUser {
    ...TransactionUserFields
  }
  tags {
    id
    name
    color
    order
  }
  ownedByUser {
    ...TransactionUserFields
  }
}
"""
)

LIST_TRANSACTIONS_QUERY = (
    """
query Web_GetTransactionsList(
  $offset: Int
  $limit: Int
  $filters: TransactionFilterInput
  $orderBy: TransactionOrdering
) {
  allTransactions(filters: $filters) {
    totalCount
    results(offset: $offset, limit: $limit, orderBy: $orderBy) {
      ...TransactionFields
    }
  }
}
"""
    + TRANSACTION_FIELDS
)

GET_TRANSACTION_QUERY = (
    """
query GetTransactionDrawer($id: UUID!, $redirectPosted: Boolean) {
  getTransaction(id: $id, redirectPosted: $redirectPosted) {
    ...TransactionFields
  }
}
"""
    + TRANSACTION_FIELDS
)

GET_TRANSACTION_SPLITS_QUERY = (
    """
query Common_TransactionSplitQuery($id: UUID!) {
  getTransaction(id: $id) {
    ...TransactionFields
    splitTransactions {
      ...TransactionSplitFields
    }
  }
}
"""
    + TRANSACTION_FIELDS
    + TRANSACTION_SPLIT_FIELDS
)

CREATE_TRANSACTION_MUTATION = """
mutation Common_CreateTransactionMutation($input: CreateTransactionMutationInput!) {
  createTransaction(input: $input) {
    transaction {
      id
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_TRANSACTION_MUTATION = (
    """
mutation Web_TransactionDrawerUpdateTransaction(
  $input: UpdateTransactionMutationInput!
) {
  updateTransaction(input: $input) {
    transaction {
      ...TransactionFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + TRANSACTION_FIELDS
)

UPDATE_TRANSACTION_SPLITS_MUTATION = (
    """
mutation Common_SplitTransactionMutation(
  $input: UpdateTransactionSplitMutationInput!
) {
  updateTransactionSplit(input: $input) {
    transaction {
      ...TransactionFields
      splitTransactions {
        ...TransactionSplitFields
      }
    }
    errors {
      message
      code
    }
  }
}
"""
    + TRANSACTION_FIELDS
    + TRANSACTION_SPLIT_FIELDS
)

DELETE_TRANSACTION_MUTATION = """
mutation Common_DeleteTransactionMutation($input: DeleteTransactionMutationInput!) {
  deleteTransaction(input: $input) {
    deleted
    errors {
      message
      code
    }
  }
}
"""

MOVE_TRANSACTION_MUTATION = """
mutation Web_MoveTransactions($input: MoveTransactionsInput!) {
  moveTransactions(input: $input) {
    numTransactionsMoved
    errors {
      message
    }
  }
}
"""

SET_TRANSACTION_TAGS_MUTATION = (
    """
mutation Web_SetTransactionTags($input: SetTransactionTagsInput!) {
  setTransactionTags(input: $input) {
    transaction {
      ...TransactionFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + TRANSACTION_FIELDS
)

LINK_TRANSACTION_TO_GOAL_MUTATION = """
mutation Common_LinkTransactionToGoal($input: LinkTransactionToGoalInput!) {
  linkTransactionToGoal(input: $input) {
    goalEvent {
      id
      transaction {
        id
        savingsGoalEvent {
          id
          goal {
            id
          }
        }
      }
    }
    errors {
      message
      code
    }
  }
}
"""


def list_transactions(
    session: AuthSession,
    *,
    filters: TransactionFilter | None = None,
    limit: int = 100,
    offset: int = 0,
    sort: TransactionSort = TransactionSort.DATE_DESCENDING,
) -> TransactionPage:
    data = graphql_request(
        session,
        "Web_GetTransactionsList",
        LIST_TRANSACTIONS_QUERY,
        {
            "offset": offset,
            "limit": limit,
            "filters": filters.to_api() if filters is not None else None,
            "orderBy": sort.value,
        },
    )
    all_transactions = _payload(data, "allTransactions")
    raw_transactions = all_transactions.get("results")
    if not isinstance(raw_transactions, list):
        raw_transactions = []
    return TransactionPage(
        transactions=[
            Transaction.from_api(transaction)
            for transaction in raw_transactions
            if isinstance(transaction, dict)
        ],
        total_count=int(all_transactions.get("totalCount") or 0),
        limit=limit,
        offset=offset,
    )


def get_transaction(
    session: AuthSession,
    transaction_id: str,
    *,
    redirect_posted: bool = True,
) -> Transaction | None:
    data = graphql_request(
        session,
        "GetTransactionDrawer",
        GET_TRANSACTION_QUERY,
        {
            "id": transaction_id,
            "redirectPosted": redirect_posted,
        },
    )
    transaction = data.get("getTransaction")
    if not isinstance(transaction, dict):
        return None
    return Transaction.from_api(transaction)


def get_transaction_splits(
    session: AuthSession,
    transaction_id: str,
) -> TransactionSplitDetails | None:
    data = graphql_request(
        session,
        "Common_TransactionSplitQuery",
        GET_TRANSACTION_SPLITS_QUERY,
        {"id": transaction_id},
    )
    transaction = data.get("getTransaction")
    if not isinstance(transaction, dict):
        return None
    return _split_details_from_transaction(transaction)


def create_transaction(
    session: AuthSession,
    *,
    account_id: str,
    amount: float,
    date: str,
    merchant_name: str,
    category_id: str,
    notes: str | None = None,
    owner_user_id: str | None = None,
    should_update_balance: bool | None = None,
    goal_id: str | None = None,
) -> Transaction:
    data = graphql_request(
        session,
        "Common_CreateTransactionMutation",
        CREATE_TRANSACTION_MUTATION,
        {
            "input": _clean(
                {
                    "accountId": account_id,
                    "amount": amount,
                    "date": date,
                    "merchantName": merchant_name,
                    "categoryId": category_id,
                    "notes": notes,
                    "ownerUserId": owner_user_id,
                    "shouldUpdateBalance": should_update_balance,
                }
            )
        },
    )
    payload = _payload(data, "createTransaction")
    _raise_payload_errors(payload)
    transaction_id = _transaction_id_payload(payload, "created")
    transaction = get_transaction(session, transaction_id)
    if transaction is None:
        raise MonarchError("Monarch created the transaction but did not return it.")
    if goal_id is not None:
        _link_transaction_to_goal(
            session,
            transaction_id,
            goal_id,
            account_id=transaction.account.id if transaction.account else account_id,
        )
        transaction = get_transaction(session, transaction_id)
        if transaction is None:
            raise MonarchError("Transaction not found after goal link.")
    return transaction


def update_transaction_splits(
    session: AuthSession,
    transaction_id: str,
    splits: Sequence[TransactionSplitDraft],
) -> TransactionSplitDetails:
    if len(splits) < 2:
        raise MonarchError("A transaction split requires at least two split rows.")

    return _update_transaction_splits(
        session,
        transaction_id,
        [split.to_api() for split in splits],
    )


def unsplit_transaction(
    session: AuthSession,
    transaction_id: str,
) -> TransactionSplitDetails:
    return _update_transaction_splits(session, transaction_id, [])


def update_transaction(
    session: AuthSession,
    transaction_id: str,
    *,
    date: str | None = None,
    amount: float | None = None,
    account_id: str | None = None,
    merchant_name: str | None = None,
    category_id: str | None = None,
    notes: str | None = None,
    hide_from_reports: bool | None = None,
    review_status: TransactionReviewStatus | None = None,
    needs_review_by_user_id: str | None = None,
    owner_user_id: str | None = None,
    tag_ids: Sequence[str] | None = None,
    goal_id: str | None = None,
    clear_goal: bool = False,
) -> Transaction:
    if goal_id is not None and clear_goal:
        raise ValueError("goal_id and clear_goal cannot both be set.")

    needs_current = account_id is not None or goal_id is not None
    current = get_transaction(session, transaction_id) if needs_current else None
    if needs_current and current is None:
        raise MonarchError("Transaction not found.")

    updates = _clean(
        {
            "id": transaction_id,
            "date": date,
            "amount": amount,
            "name": merchant_name,
            "category": category_id,
            "notes": notes,
            "hideFromReports": hide_from_reports,
            "reviewStatus": (
                review_status.value if review_status is not None else None
            ),
            "needsReviewByUser": needs_review_by_user_id,
            "ownerUserId": owner_user_id,
        }
    )
    updated_transaction: Transaction | None = None
    if len(updates) > 1:
        data = graphql_request(
            session,
            "Web_TransactionDrawerUpdateTransaction",
            UPDATE_TRANSACTION_MUTATION,
            {"input": updates},
        )
        payload = _payload(data, "updateTransaction")
        _raise_payload_errors(payload)
        updated_transaction = _transaction_payload(payload, "updated")

    if account_id is not None:
        _move_transaction(session, transaction_id, account_id, current)
        updated_transaction = get_transaction(session, transaction_id)
        if updated_transaction is None:
            raise MonarchError("Transaction not found after account update.")

    if tag_ids is not None:
        updated_transaction = _update_transaction_tags(session, transaction_id, tag_ids)

    if clear_goal:
        _link_transaction_to_goal(session, transaction_id, None)
        updated_transaction = get_transaction(session, transaction_id)
        if updated_transaction is None:
            raise MonarchError("Transaction not found after goal unlink.")

    if goal_id is not None:
        account = (
            updated_transaction.account
            if updated_transaction is not None
            else current.account if current is not None else None
        )
        _link_transaction_to_goal(
            session,
            transaction_id,
            goal_id,
            account_id=account.id if account is not None else None,
        )
        updated_transaction = get_transaction(session, transaction_id)
        if updated_transaction is None:
            raise MonarchError("Transaction not found after goal link.")

    if updated_transaction is not None:
        return updated_transaction

    transaction = get_transaction(session, transaction_id)
    if transaction is None:
        raise MonarchError("Transaction not found.")
    return transaction


def delete_transaction(
    session: AuthSession,
    transaction_id: str,
) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteTransactionMutation",
        DELETE_TRANSACTION_MUTATION,
        {"input": {"transactionId": transaction_id}},
    )
    payload = _payload(data, "deleteTransaction")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


def _update_transaction_splits(
    session: AuthSession,
    transaction_id: str,
    split_data: list[JsonDict],
) -> TransactionSplitDetails:
    data = graphql_request(
        session,
        "Common_SplitTransactionMutation",
        UPDATE_TRANSACTION_SPLITS_MUTATION,
        {
            "input": {
                "transactionId": transaction_id,
                "splitData": split_data,
            }
        },
    )
    payload = _payload(data, "updateTransactionSplit")
    _raise_payload_errors(payload)
    transaction = payload.get("transaction")
    if not isinstance(transaction, dict):
        raise MonarchError("Monarch did not return the updated transaction splits.")
    return _split_details_from_transaction(transaction)


def _update_transaction_tags(
    session: AuthSession,
    transaction_id: str,
    tag_ids: Sequence[str],
) -> Transaction:
    data = graphql_request(
        session,
        "Web_SetTransactionTags",
        SET_TRANSACTION_TAGS_MUTATION,
        {
            "input": {
                "transactionId": transaction_id,
                "tagIds": list(tag_ids),
            }
        },
    )
    payload = _payload(data, "setTransactionTags")
    _raise_payload_errors(payload)
    return _transaction_payload(payload, "updated")


def _link_transaction_to_goal(
    session: AuthSession,
    transaction_id: str,
    goal_id: str | None,
    *,
    account_id: str | None = None,
) -> None:
    data = graphql_request(
        session,
        "Common_LinkTransactionToGoal",
        LINK_TRANSACTION_TO_GOAL_MUTATION,
        {
            "input": _clean(
                {
                    "transactionId": transaction_id,
                    "goalId": goal_id,
                    "accountId": account_id,
                }
            )
        },
    )
    payload = _payload(data, "linkTransactionToGoal")
    _raise_payload_errors(payload)


def _split_details_from_transaction(data: JsonDict) -> TransactionSplitDetails:
    raw_splits = data.get("splitTransactions")
    if not isinstance(raw_splits, list):
        raw_splits = []
    return TransactionSplitDetails(
        transaction=Transaction.from_api(data),
        splits=[
            TransactionSplit.from_api(split)
            for split in raw_splits
            if isinstance(split, dict)
        ],
    )


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


def _move_transaction(
    session: AuthSession,
    transaction_id: str,
    to_account_id: str,
    current: Transaction | None,
) -> None:
    if current is None or current.account is None:
        raise MonarchError("Transaction account is required to move a transaction.")
    if current.account.id == to_account_id:
        return

    data = graphql_request(
        session,
        "Web_MoveTransactions",
        MOVE_TRANSACTION_MUTATION,
        {
            "input": {
                "fromAccountId": current.account.id,
                "toAccountId": to_account_id,
                "selectedTransactionIds": [transaction_id],
                "excludedTransactionIds": [],
                "isAllSelected": False,
                "expectedAffectedTransactionCount": 1,
            }
        },
    )
    payload = _payload(data, "moveTransactions")
    _raise_payload_errors(payload)
    if payload.get("numTransactionsMoved") not in (None, 1):
        raise MonarchError("Monarch did not move exactly one transaction.")


def _raise_payload_errors(payload: JsonDict) -> None:
    errors = payload.get("errors")
    if not errors:
        return
    if isinstance(errors, list):
        messages = []
        for error in errors:
            if isinstance(error, dict):
                messages.append(str(error.get("message") or error))
            elif error:
                messages.append(str(error))
        raise MonarchError("; ".join(messages) or "Monarch request failed.")
    if isinstance(errors, dict):
        raise MonarchError(str(errors.get("message") or errors))
    raise MonarchError(str(errors))


def _transaction_id_payload(payload: JsonDict, action: str) -> str:
    transaction = payload.get("transaction")
    if not isinstance(transaction, dict) or transaction.get("id") is None:
        raise MonarchError(f"Monarch did not return the {action} transaction.")
    return str(transaction["id"])


def _transaction_payload(payload: JsonDict, action: str) -> Transaction:
    transaction = payload.get("transaction")
    if not isinstance(transaction, dict):
        raise MonarchError(f"Monarch did not return the {action} transaction.")
    return Transaction.from_api(transaction)
