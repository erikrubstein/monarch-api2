from __future__ import annotations

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.merchants import Merchant, MerchantSort


MERCHANT_LIST_FIELDS = """
fragment MerchantListFields on Merchant {
  id
  name
  logoUrl
  transactionCount
  createdAt
  recurringTransactionStream {
    id
  }
}
"""

MERCHANT_FIELDS = """
fragment MerchantFields on Merchant {
  id
  name
  logoUrl
  transactionCount
  ruleCount
  canBeDeleted
  createdAt
  recurringTransactionStream {
    id
  }
}
"""

LIST_MERCHANTS_QUERY = (
    """
query Common_ListMerchants(
  $search: String
  $limit: Int
  $offset: Int
  $orderBy: MerchantOrdering
) {
  merchants(
    search: $search
    limit: $limit
    offset: $offset
    orderBy: $orderBy
  ) {
    ...MerchantListFields
  }
}
"""
    + MERCHANT_LIST_FIELDS
)

GET_MERCHANT_QUERY = (
    """
query Common_GetEditMerchant($merchantId: ID!) {
  merchant(id: $merchantId) {
    ...MerchantFields
  }
}
"""
    + MERCHANT_FIELDS
)

UPDATE_MERCHANT_MUTATION = (
    """
mutation Common_UpdateMerchant($input: UpdateMerchantInput!) {
  updateMerchant(input: $input) {
    merchant {
      ...MerchantFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + MERCHANT_FIELDS
)

DELETE_MERCHANT_MUTATION = """
mutation Common_DeleteMerchant($merchantId: ID!, $moveToId: ID) {
  deleteMerchant(id: $merchantId, moveRelationsToMerchantId: $moveToId) {
    success
  }
}
"""


def list_merchants(
    session: AuthSession,
    *,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort: MerchantSort = MerchantSort.TRANSACTION_COUNT,
) -> list[Merchant]:
    data = graphql_request(
        session,
        "Common_ListMerchants",
        LIST_MERCHANTS_QUERY,
        {
            "search": search,
            "limit": limit,
            "offset": offset,
            "orderBy": sort.value,
        },
    )
    raw_merchants = data.get("merchants")
    if not isinstance(raw_merchants, list):
        return []
    return [
        Merchant.from_api(merchant)
        for merchant in raw_merchants
        if isinstance(merchant, dict)
    ]


def get_merchant(session: AuthSession, merchant_id: str) -> Merchant | None:
    data = graphql_request(
        session,
        "Common_GetEditMerchant",
        GET_MERCHANT_QUERY,
        {"merchantId": merchant_id},
    )
    merchant = data.get("merchant")
    if not isinstance(merchant, dict):
        return None
    return Merchant.from_api(merchant)


def update_merchant(
    session: AuthSession,
    merchant_id: str,
    *,
    name: str | None = None,
) -> Merchant:
    if name is None:
        current = get_merchant(session, merchant_id)
        if current is None:
            raise MonarchError("Merchant not found.")
        return current

    data = graphql_request(
        session,
        "Common_UpdateMerchant",
        UPDATE_MERCHANT_MUTATION,
        {
            "input": {
                "merchantId": merchant_id,
                "name": name,
            }
        },
    )
    payload = _payload(data, "updateMerchant")
    _raise_payload_errors(payload)
    return _merchant_payload(payload, "updated")


def delete_merchant(
    session: AuthSession,
    merchant_id: str,
    *,
    move_to_merchant_id: str | None = None,
) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteMerchant",
        DELETE_MERCHANT_MUTATION,
        {
            "merchantId": merchant_id,
            "moveToId": move_to_merchant_id,
        },
    )
    payload = _payload(data, "deleteMerchant")
    return bool(payload.get("success"))


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


def _merchant_payload(payload: JsonDict, action: str) -> Merchant:
    merchant = payload.get("merchant")
    if not isinstance(merchant, dict):
        raise MonarchError(f"Monarch did not return the {action} merchant.")
    return Merchant.from_api(merchant)


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
