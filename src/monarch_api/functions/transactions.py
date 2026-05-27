from __future__ import annotations

from collections.abc import Sequence
import mimetypes
from pathlib import Path

import httpx

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    Transaction,
    TransactionAttachment,
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

TRANSACTION_ATTACHMENT_FIELDS = """
fragment TransactionAttachmentFields on TransactionAttachment {
  id
  publicId
  extension
  sizeBytes
  filename
  originalAssetUrl
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
    ...TransactionAttachmentFields
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
    + TRANSACTION_ATTACHMENT_FIELDS
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

GET_TRANSACTION_ATTACHMENT_QUERY = (
    """
query Mobile_GetAttachmentDetails($attachmentId: UUID!) {
  transactionAttachment(id: $attachmentId) {
    ...TransactionAttachmentFields
  }
}
"""
    + TRANSACTION_ATTACHMENT_FIELDS
)

GET_TRANSACTION_ATTACHMENT_UPLOAD_INFO_MUTATION = """
mutation Common_GetTransactionAttachmentUploadInfo($transactionId: UUID!) {
  getTransactionAttachmentUploadInfo(transactionId: $transactionId) {
    info {
      path
      requestParams {
        timestamp
        folder
        signature
        api_key
        upload_preset
      }
    }
  }
}
"""

ADD_TRANSACTION_ATTACHMENT_MUTATION = (
    """
mutation Common_AddTransactionAttachment(
  $input: TransactionAddAttachmentMutationInput!
) {
  addTransactionAttachment(input: $input) {
    attachment {
      ...TransactionAttachmentFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + TRANSACTION_ATTACHMENT_FIELDS
)

DELETE_TRANSACTION_ATTACHMENT_MUTATION = """
mutation Web_TransactionDrawerDeleteAttachment($id: UUID!) {
  deleteTransactionAttachment(id: $id) {
    deleted
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


def list_transaction_attachments(
    session: AuthSession,
    transaction_id: str,
    *,
    redirect_posted: bool = True,
) -> list[TransactionAttachment]:
    transaction = get_transaction(
        session,
        transaction_id,
        redirect_posted=redirect_posted,
    )
    if transaction is None:
        raise MonarchError("Transaction not found.")
    return transaction.attachments


def get_transaction_attachment(
    session: AuthSession,
    attachment_id: str,
) -> TransactionAttachment | None:
    data = graphql_request(
        session,
        "Mobile_GetAttachmentDetails",
        GET_TRANSACTION_ATTACHMENT_QUERY,
        {"attachmentId": attachment_id},
    )
    attachment = data.get("transactionAttachment")
    if not isinstance(attachment, dict):
        return None
    return TransactionAttachment.from_api(attachment)


def upload_transaction_attachment(
    session: AuthSession,
    transaction_id: str,
    file_path: str | Path,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> TransactionAttachment:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    upload_info = _get_attachment_upload_info(session, transaction_id)
    upload_result = _upload_attachment_file(
        upload_info,
        path,
        filename=filename,
        content_type=content_type,
    )
    public_id = upload_result.get("public_id")
    if not public_id:
        raise MonarchError("Cloudinary upload did not return a public id.")

    upload_filename = filename or path.name
    data = graphql_request(
        session,
        "Common_AddTransactionAttachment",
        ADD_TRANSACTION_ATTACHMENT_MUTATION,
        {
            "input": {
                "transactionId": transaction_id,
                "filename": Path(upload_filename).stem,
                "publicId": str(public_id),
                "extension": Path(upload_filename).suffix.lstrip("."),
                "sizeBytes": path.stat().st_size,
            }
        },
    )
    payload = _payload(data, "addTransactionAttachment")
    _raise_payload_errors(payload)
    attachment = TransactionAttachment.from_api(payload.get("attachment"))
    if attachment is None:
        raise MonarchError("Monarch did not return the uploaded attachment.")
    return attachment


def download_transaction_attachment(
    session: AuthSession,
    attachment_id: str,
    path: str | Path | None = None,
) -> bytes:
    attachment = get_transaction_attachment(session, attachment_id)
    if attachment is None:
        raise MonarchError("Transaction attachment not found.")
    if not attachment.original_asset_url:
        raise MonarchError("Transaction attachment did not include a download URL.")

    try:
        response = httpx.get(attachment.original_asset_url, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise MonarchError(f"Failed to download transaction attachment: {error}") from error

    content = response.content
    if path is not None:
        download_path = Path(path)
        if download_path.exists() and download_path.is_dir():
            download_path = download_path / _attachment_filename(attachment)
        download_path.parent.mkdir(parents=True, exist_ok=True)
        download_path.write_bytes(content)
    return content


def delete_transaction_attachment(
    session: AuthSession,
    attachment_id: str,
) -> bool:
    data = graphql_request(
        session,
        "Web_TransactionDrawerDeleteAttachment",
        DELETE_TRANSACTION_ATTACHMENT_MUTATION,
        {"id": attachment_id},
    )
    payload = _payload(data, "deleteTransactionAttachment")
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


def _get_attachment_upload_info(
    session: AuthSession,
    transaction_id: str,
) -> JsonDict:
    data = graphql_request(
        session,
        "Common_GetTransactionAttachmentUploadInfo",
        GET_TRANSACTION_ATTACHMENT_UPLOAD_INFO_MUTATION,
        {"transactionId": transaction_id},
    )
    payload = _payload(data, "getTransactionAttachmentUploadInfo")
    info = payload.get("info")
    if not isinstance(info, dict):
        raise MonarchError("Monarch did not return attachment upload info.")
    return info


def _upload_attachment_file(
    upload_info: JsonDict,
    path: Path,
    *,
    filename: str | None,
    content_type: str | None,
) -> JsonDict:
    upload_path = upload_info.get("path")
    request_params = upload_info.get("requestParams")
    if not isinstance(upload_path, str) or not isinstance(request_params, dict):
        raise MonarchError("Monarch returned invalid attachment upload info.")

    upload_filename = filename or path.name
    guessed_content_type = mimetypes.guess_type(upload_filename)[0]
    form_data = {
        key: str(value)
        for key, value in request_params.items()
        if key != "__typename" and value is not None
    }
    files = {
        "file": (
            upload_filename,
            path.read_bytes(),
            content_type or guessed_content_type or "application/octet-stream",
        )
    }
    url = _cloudinary_upload_url(upload_path)
    try:
        response = httpx.post(url, data=form_data, files=files, timeout=60.0)
    except httpx.HTTPError as error:
        raise MonarchError(f"Failed to upload transaction attachment: {error}") from error
    data = response.json()
    if response.status_code >= 400:
        message = data.get("error") if isinstance(data, dict) else None
        if isinstance(message, dict):
            raise MonarchError(str(message.get("message") or message))
        raise MonarchError("Failed to upload transaction attachment.")
    if not isinstance(data, dict):
        raise MonarchError("Cloudinary upload response was not a JSON object.")
    return data


def _cloudinary_upload_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"https://api.cloudinary.com{path}"


def _attachment_filename(attachment: TransactionAttachment) -> str:
    filename = attachment.filename or attachment.id
    extension = attachment.extension
    if extension and not filename.endswith(f".{extension}"):
        return f"{filename}.{extension}"
    return filename


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
