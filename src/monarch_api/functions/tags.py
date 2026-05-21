from __future__ import annotations

from collections.abc import Iterable

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.tags import Tag


TAG_FIELDS = """
fragment TagFields on TransactionTag {
  id
  name
  color
  order
  transactionCount @include(if: $includeTransactionCount)
}
"""

LIST_TAGS_QUERY = (
    """
query Common_GetHouseholdTransactionTags(
  $search: String
  $limit: Int
  $includeTransactionCount: Boolean = false
) {
  householdTransactionTags(search: $search, limit: $limit) {
    ...TagFields
  }
}
"""
    + TAG_FIELDS
)

CREATE_TAG_MUTATION = (
    """
mutation Common_CreateTransactionTag(
  $input: CreateTransactionTagInput!
  $includeTransactionCount: Boolean = true
) {
  createTransactionTag(input: $input) {
    tag {
      ...TagFields
    }
    errors {
      message
    }
  }
}
"""
    + TAG_FIELDS
)

UPDATE_TAG_MUTATION = (
    """
mutation Common_UpdateTransactionTag(
  $input: UpdateTransactionTagInput!
  $includeTransactionCount: Boolean = true
) {
  updateTransactionTag(input: $input) {
    tag {
      ...TagFields
    }
    errors {
      message
    }
  }
}
"""
    + TAG_FIELDS
)

DELETE_TAG_MUTATION = """
mutation Common_DeleteHouseholdTransactionTag($tagId: ID!) {
  deleteTransactionTag(tagId: $tagId) {
    errors {
      message
      code
    }
  }
}
"""

REORDER_TAG_MUTATION = (
    """
mutation Common_UpdateTransactionTagOrder(
  $tagId: ID!
  $order: Int!
  $includeTransactionCount: Boolean = true
) {
  updateTransactionTagOrder(tagId: $tagId, order: $order) {
    householdTransactionTags {
      ...TagFields
    }
  }
}
"""
    + TAG_FIELDS
)


def list_tags(
    session: AuthSession,
    *,
    search: str | None = None,
    limit: int | None = None,
    include_transaction_count: bool = False,
) -> list[Tag]:
    data = graphql_request(
        session,
        "Common_GetHouseholdTransactionTags",
        LIST_TAGS_QUERY,
        {
            "search": search,
            "limit": limit,
            "includeTransactionCount": include_transaction_count,
        },
    )
    raw_tags = data.get("householdTransactionTags")
    if not isinstance(raw_tags, list):
        return []
    return _sort_tags(
        Tag.from_api(tag)
        for tag in raw_tags
        if isinstance(tag, dict)
    )


def get_tag(session: AuthSession, tag_id: str) -> Tag | None:
    for tag in list_tags(session, include_transaction_count=True):
        if tag.id == tag_id:
            return tag
    return None


def create_tag(
    session: AuthSession,
    *,
    name: str,
    color: str,
) -> Tag:
    data = graphql_request(
        session,
        "Common_CreateTransactionTag",
        CREATE_TAG_MUTATION,
        {
            "input": {
                "name": name,
                "color": color,
            },
            "includeTransactionCount": True,
        },
    )
    payload = _payload(data, "createTransactionTag")
    _raise_payload_errors(payload)
    return _tag_payload(payload, "created")


def update_tag(
    session: AuthSession,
    tag_id: str,
    *,
    name: str | None = None,
    color: str | None = None,
) -> Tag:
    current = get_tag(session, tag_id)
    if current is None:
        raise MonarchError("Tag not found.")

    data = graphql_request(
        session,
        "Common_UpdateTransactionTag",
        UPDATE_TAG_MUTATION,
        {
            "input": {
                "id": tag_id,
                "name": name if name is not None else current.name,
                "color": color if color is not None else current.color,
            },
            "includeTransactionCount": True,
        },
    )
    payload = _payload(data, "updateTransactionTag")
    _raise_payload_errors(payload)
    return _tag_payload(payload, "updated")


def delete_tag(session: AuthSession, tag_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteHouseholdTransactionTag",
        DELETE_TAG_MUTATION,
        {"tagId": tag_id},
    )
    payload = _payload(data, "deleteTransactionTag")
    _raise_payload_errors(payload)
    return True


def reorder_tag(
    session: AuthSession,
    tag_id: str,
    *,
    order: int,
) -> list[Tag]:
    data = graphql_request(
        session,
        "Common_UpdateTransactionTagOrder",
        REORDER_TAG_MUTATION,
        {
            "tagId": tag_id,
            "order": order,
            "includeTransactionCount": True,
        },
    )
    payload = _payload(data, "updateTransactionTagOrder")
    raw_tags = payload.get("householdTransactionTags")
    if not isinstance(raw_tags, list):
        return []
    return _sort_tags(
        Tag.from_api(tag)
        for tag in raw_tags
        if isinstance(tag, dict)
    )


def _sort_tags(tags: Iterable[Tag]) -> list[Tag]:
    return sorted(
        tags,
        key=lambda tag: (
            tag.order if isinstance(tag.order, int) else _SORT_LAST,
            tag.name.casefold(),
            tag.id,
        ),
    )


_SORT_LAST = 1_000_000


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


def _tag_payload(payload: JsonDict, action: str) -> Tag:
    tag = payload.get("tag")
    if not isinstance(tag, dict):
        raise MonarchError(f"Monarch did not return the {action} tag.")
    return Tag.from_api(tag)


def _raise_payload_errors(payload: JsonDict) -> None:
    errors = payload.get("errors")
    if not errors:
        return
    if isinstance(errors, list):
        messages = [
            str(error.get("message") or error)
            for error in errors
            if isinstance(error, dict) or error
        ]
        raise MonarchError("; ".join(messages) or "Monarch request failed.")
    if isinstance(errors, dict):
        raise MonarchError(str(errors.get("message") or errors))
    raise MonarchError(str(errors))
