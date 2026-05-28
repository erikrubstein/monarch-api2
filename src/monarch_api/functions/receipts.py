from __future__ import annotations

import json
import mimetypes
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

import httpx

from monarch_api.functions.common import (
    API_BASE_URL,
    MonarchError,
    build_auth_headers,
    graphql_request,
)
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.receipts import (
    Receipt,
    ReceiptFilter,
    ReceiptLineItemUpdate,
    ReceiptPage,
    ReceiptSettings,
)


RECEIPT_FIELDS = """
fragment ReceiptFields on RetailSync {
  id
  vendor
  status
  startedAt
  endedAt
  createdAt
  updatedAt
  orders {
    id
    merchantName
    vendor
    vendorOrderId
    date
    totalForProducts
    shipping
    deliveryFee
    additionalCharges
    adjustmentsAmount
    totalBeforeTax
    tax
    tip
    giftCardAmount
    grandTotal
    displayStatus
    retailLineItems {
      id
      title
      quantity
      price
      total
      isAssociatedToRetailTransaction
      category {
        id
        name
        icon
      }
    }
    retailTransactions {
      id
      date
      total
      transactionType
      transactionUpdateSkipped
      transaction {
        id
        isManual
        hasSplitTransactions
        merchant {
          id
          name
          logoUrl
        }
      }
    }
  }
  attachments {
    id
    storageId
    filename
    extension
    sizeBytes
    originalAssetUrl
    thumbnailUrl
  }
}
"""

LIST_RECEIPTS_QUERY = (
    """
query Common_RetailSyncsQueryWithTotal(
  $filters: RetailSyncFilterInput!
  $offset: Int!
  $limit: Int!
  $includeTotalCount: Boolean
) {
  retailSyncsWithTotal(
    filters: $filters
    offset: $offset
    limit: $limit
    includeTotalCount: $includeTotalCount
  ) {
    totalCount
    results {
      ...ReceiptFields
    }
  }
}
"""
    + RECEIPT_FIELDS
)

GET_RECEIPT_QUERY = (
    """
query Common_RetailSyncQuery($syncId: ID!) {
  retailSync(id: $syncId) {
    ...ReceiptFields
  }
}
"""
    + RECEIPT_FIELDS
)

CREATE_RECEIPT_MUTATION = """
mutation Common_CreateRetailSync($input: CreateRetailSyncInput!) {
  createRetailSync(input: $input) {
    retailSync {
      id
      vendor
      status
      startedAt
      endedAt
      createdAt
      updatedAt
    }
    errors {
      message
      code
    }
  }
}
"""

START_RECEIPT_MUTATION = """
mutation Common_StartRetailSync($syncId: ID!) {
  startRetailSync(id: $syncId) {
    retailSync {
      id
      vendor
      status
      startedAt
      endedAt
      createdAt
      updatedAt
    }
    errors {
      message
      code
    }
  }
}
"""

DELETE_RECEIPT_MUTATION = """
mutation Common_DeleteRetailSync($syncId: ID!) {
  deleteUnmatchedRetailSync(id: $syncId) {
    success
    errors {
      message
      code
    }
  }
}
"""

MATCH_RECEIPT_MUTATION = """
mutation Common_MatchRetailTransaction(
  $retailTransactionId: ID!
  $transactionId: ID!
) {
  matchRetailTransaction(
    retailTransactionId: $retailTransactionId
    transactionId: $transactionId
  ) {
    retailSync {
      id
    }
    errors {
      message
      code
    }
  }
}
"""

UNMATCH_RECEIPT_MUTATION = """
mutation Web_UnmatchRetailTransaction($retailTransactionId: ID!) {
  unmatchRetailTransaction(retailTransactionId: $retailTransactionId) {
    retailSync {
      id
      status
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_RECEIPT_MUTATION = (
    """
mutation Common_UpdateRetailOrder($input: UpdateRetailOrderInput!) {
  updateRetailOrder(input: $input) {
    retailSync {
      ...ReceiptFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + RECEIPT_FIELDS
)

GET_RECEIPT_SETTINGS_QUERY = """
query Common_GetRetailExtensionSettings {
  retailExtensionSettings {
    id
    retailVendorSettings {
      id
      vendor
      shouldCategorizeAndSplitTransactions
      shouldUpdateTransactionsNotes
    }
  }
}
"""

UPDATE_RECEIPT_SETTINGS_MUTATION = """
mutation Common_UpdateRetailVendorSettings($input: UpdateRetailVendorSettingsInput!) {
  updateRetailVendorSettings(input: $input) {
    retailVendorSettings {
      id
      vendor
      shouldCategorizeAndSplitTransactions
      shouldUpdateTransactionsNotes
    }
    errors {
      message
      code
    }
  }
}
"""


def list_receipts(
    session: AuthSession,
    *,
    filters: ReceiptFilter | None = None,
    limit: int = 100,
    offset: int = 0,
) -> ReceiptPage:
    receipt_filters = (
        filters.to_api() if filters is not None else {"vendor": "user_import"}
    )
    data = graphql_request(
        session,
        "Common_RetailSyncsQueryWithTotal",
        LIST_RECEIPTS_QUERY,
        {
            "filters": receipt_filters,
            "offset": offset,
            "limit": limit,
            "includeTotalCount": True,
        },
    )
    payload = _payload(data, "retailSyncsWithTotal")
    raw_receipts = payload.get("results")
    if not isinstance(raw_receipts, list):
        raw_receipts = []
    return ReceiptPage(
        receipts=[
            Receipt.from_api(receipt)
            for receipt in raw_receipts
            if isinstance(receipt, dict)
        ],
        total_count=int(payload.get("totalCount") or 0),
        limit=limit,
        offset=offset,
    )


def get_receipt(
    session: AuthSession,
    receipt_id: str,
) -> Receipt | None:
    data = graphql_request(
        session,
        "Common_RetailSyncQuery",
        GET_RECEIPT_QUERY,
        {"syncId": receipt_id},
    )
    receipt = data.get("retailSync")
    if not isinstance(receipt, dict):
        return None
    return Receipt.from_api(receipt)


def upload_receipt(
    session: AuthSession,
    file_path: str | Path,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> Receipt:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    receipt = _create_receipt_sync(session)
    _upload_receipt_file(
        session,
        receipt.id,
        path,
        filename=filename,
        content_type=content_type,
    )
    started = _start_receipt_processing(session, receipt.id)
    return _refetched_receipt_or_fallback(session, receipt.id, started)


def delete_receipt(
    session: AuthSession,
    receipt_id: str,
) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteRetailSync",
        DELETE_RECEIPT_MUTATION,
        {"syncId": receipt_id},
    )
    payload = _payload(data, "deleteUnmatchedRetailSync")
    _raise_payload_errors(payload)
    return bool(payload.get("success"))


def match_receipt(
    session: AuthSession,
    receipt_id: str,
    transaction_id: str,
) -> Receipt:
    receipt_transaction_id = _receipt_transaction_id(session, receipt_id)
    data = graphql_request(
        session,
        "Common_MatchRetailTransaction",
        MATCH_RECEIPT_MUTATION,
        {
            "retailTransactionId": receipt_transaction_id,
            "transactionId": transaction_id,
        },
    )
    payload = _payload(data, "matchRetailTransaction")
    _raise_payload_errors(payload)
    return _refetched_receipt(session, receipt_id, "matched")


def unmatch_receipt(
    session: AuthSession,
    receipt_id: str,
) -> Receipt:
    receipt_transaction_id = _receipt_transaction_id(session, receipt_id)
    data = graphql_request(
        session,
        "Web_UnmatchRetailTransaction",
        UNMATCH_RECEIPT_MUTATION,
        {"retailTransactionId": receipt_transaction_id},
    )
    payload = _payload(data, "unmatchRetailTransaction")
    _raise_payload_errors(payload)
    return _refetched_receipt(session, receipt_id, "unmatched")


def update_receipt(
    session: AuthSession,
    receipt_id: str,
    *,
    merchant_name: str | None = None,
    date: str | None = None,
    total_before_tax: float | None = None,
    tax: float | None = None,
    tip: float | None = None,
    grand_total: float | None = None,
    line_items: Sequence[ReceiptLineItemUpdate] | None = None,
    transaction_date: str | None = None,
    transaction_total: float | None = None,
) -> Receipt:
    receipt = get_receipt(session, receipt_id)
    if receipt is None:
        raise MonarchError("Receipt not found.")
    if receipt.order is None:
        raise MonarchError("Receipt does not include an order to update.")

    transaction_updates: list[JsonDict] | None = None
    if transaction_date is not None or transaction_total is not None:
        if receipt.transaction is None:
            raise MonarchError("Receipt does not include a transaction to update.")
        transaction_updates = [
            _clean(
                {
                    "retailTransactionId": receipt.transaction.id,
                    "date": transaction_date,
                    "total": transaction_total,
                }
            )
        ]

    data = graphql_request(
        session,
        "Common_UpdateRetailOrder",
        UPDATE_RECEIPT_MUTATION,
        {
            "input": _clean(
                {
                    "retailOrderId": receipt.order.id,
                    "merchantName": merchant_name,
                    "date": date,
                    "totalBeforeTax": total_before_tax,
                    "tax": tax,
                    "tip": tip,
                    "grandTotal": grand_total,
                    "lineItemUpdates": (
                        [item.to_api() for item in line_items]
                        if line_items is not None
                        else None
                    ),
                    "transactionUpdates": transaction_updates,
                }
            )
        },
    )
    payload = _payload(data, "updateRetailOrder")
    _raise_payload_errors(payload)
    receipt = Receipt.from_api(_payload(payload, "retailSync"))
    return receipt


def get_receipt_settings(session: AuthSession) -> ReceiptSettings:
    data = graphql_request(
        session,
        "Common_GetRetailExtensionSettings",
        GET_RECEIPT_SETTINGS_QUERY,
    )
    settings = _receipt_vendor_settings(data)
    return ReceiptSettings.from_api(settings)


def update_receipt_settings(
    session: AuthSession,
    *,
    auto_categorize: bool | None = None,
    update_transaction_notes: bool | None = None,
) -> ReceiptSettings:
    data = graphql_request(
        session,
        "Common_UpdateRetailVendorSettings",
        UPDATE_RECEIPT_SETTINGS_MUTATION,
        {
            "input": _clean(
                {
                    "vendor": "user_import",
                    "shouldCategorizeAndSplitTransactions": auto_categorize,
                    "shouldUpdateTransactionsNotes": update_transaction_notes,
                }
            )
        },
    )
    payload = _payload(data, "updateRetailVendorSettings")
    _raise_payload_errors(payload)
    settings = payload.get("retailVendorSettings")
    if not isinstance(settings, dict):
        raise MonarchError("Monarch did not return receipt settings.")
    return ReceiptSettings.from_api(settings)


def _receipt_transaction_id(
    session: AuthSession,
    receipt_id: str,
) -> str:
    receipt = get_receipt(session, receipt_id)
    if receipt is None:
        raise MonarchError("Receipt not found.")
    if receipt.transaction is None:
        raise MonarchError("Receipt does not include a transaction to match.")
    return receipt.transaction.id


def _create_receipt_sync(session: AuthSession) -> Receipt:
    data = graphql_request(
        session,
        "Common_CreateRetailSync",
        CREATE_RECEIPT_MUTATION,
        {"input": {"vendor": "user_import", "isBackfill": False}},
    )
    payload = _payload(data, "createRetailSync")
    _raise_payload_errors(payload)
    receipt = payload.get("retailSync")
    if not isinstance(receipt, dict):
        raise MonarchError("Monarch did not return the created receipt.")
    return Receipt.from_api(receipt)


def _upload_receipt_file(
    session: AuthSession,
    receipt_id: str,
    path: Path,
    *,
    filename: str | None,
    content_type: str | None,
) -> None:
    upload_filename = filename or path.name
    upload_content_type = (
        content_type
        or mimetypes.guess_type(upload_filename)[0]
        or "application/octet-stream"
    )
    metadata = {
        "orderId": str(uuid4()),
        "vendor": "user_import",
        "payloadType": "order",
        "contentType": upload_content_type,
    }
    form_data = {
        "payloads_count": "1",
        "metadata_0": json.dumps(metadata, separators=(",", ":")),
    }
    files = {
        "payload_0": (
            upload_filename,
            path.read_bytes(),
            upload_content_type,
        )
    }
    url = f"{API_BASE_URL}/retail-sync/{receipt_id}/files"
    try:
        response = httpx.post(
            url,
            data=form_data,
            files=files,
            headers=build_auth_headers(session),
            timeout=60.0,
        )
    except httpx.HTTPError as error:
        raise MonarchError(f"Failed to upload receipt file: {error}") from error
    if response.status_code >= 400:
        message = _response_error_message(response, "Failed to upload receipt.")
        raise MonarchError(message)


def _start_receipt_processing(session: AuthSession, receipt_id: str) -> Receipt:
    data = graphql_request(
        session,
        "Common_StartRetailSync",
        START_RECEIPT_MUTATION,
        {"syncId": receipt_id},
    )
    payload = _payload(data, "startRetailSync")
    _raise_payload_errors(payload)
    receipt = payload.get("retailSync")
    if not isinstance(receipt, dict):
        raise MonarchError("Monarch did not return the started receipt.")
    return Receipt.from_api(receipt)


def _refetched_receipt_or_fallback(
    session: AuthSession,
    receipt_id: str,
    fallback: Receipt,
) -> Receipt:
    try:
        receipt = get_receipt(session, receipt_id)
    except MonarchError:
        return fallback
    return receipt or fallback


def _refetched_receipt(
    session: AuthSession,
    receipt_id: str,
    action: str,
) -> Receipt:
    receipt = get_receipt(session, receipt_id)
    if receipt is None:
        raise MonarchError(f"Receipt not found after it was {action}.")
    return receipt


def _receipt_vendor_settings(data: JsonDict) -> JsonDict | None:
    extension_settings = data.get("retailExtensionSettings")
    if not isinstance(extension_settings, dict):
        return None
    vendor_settings = extension_settings.get("retailVendorSettings")
    if not isinstance(vendor_settings, list):
        return None
    for settings in vendor_settings:
        if isinstance(settings, dict) and settings.get("vendor") == "user_import":
            return settings
    return None


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


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


def _response_error_message(response: httpx.Response, fallback: str) -> str:
    try:
        data = response.json()
    except ValueError:
        return fallback
    if not isinstance(data, dict):
        return fallback
    error = data.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(data.get("detail") or data.get("message") or error or fallback)
