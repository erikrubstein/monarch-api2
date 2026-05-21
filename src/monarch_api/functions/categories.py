from __future__ import annotations

from typing import TypedDict

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.categories import (
    Category,
    CategoryCatalog,
    CategoryFilter,
    CategoryGroup,
    CategoryType,
)
from monarch_api.types.common import JsonDict


class _CategoryData(TypedDict):
    categories: list[Category]
    category_groups: list[JsonDict]


CATEGORY_FIELDS = """
fragment CategoryFields on Category {
  id
  order
  name
  icon
  systemCategory
  systemCategoryDisplayName
  isSystemCategory
  isDisabled
  isProtected
  excludeFromBudget
  budgetVariability
  group {
    id
    name
    type
  }
}
"""

CATEGORY_GROUP_FIELDS = """
fragment CategoryGroupFields on CategoryGroup {
  id
  name
  order
  type
  color
  groupLevelBudgetingEnabled
  budgetVariability
}
"""

LIST_CATEGORIES_QUERY = (
    """
query Common_GetCategories($includeSystemDisabledCategories: Boolean) {
  categories(includeDisabledSystemCategories: $includeSystemDisabledCategories) {
    ...CategoryFields
  }
}
"""
    + CATEGORY_FIELDS
)

LIST_CATEGORY_GROUPS_QUERY = (
    """
query Common_GetCategoryGroups {
  categoryGroups {
    ...CategoryGroupFields
  }
}
"""
    + CATEGORY_GROUP_FIELDS
)

GET_CATEGORY_CATALOG_QUERY = (
    """
query Common_GetCategories($includeSystemDisabledCategories: Boolean) {
  categoryGroups {
    ...CategoryGroupFields
    categories {
      id
    }
  }
  categories(includeDisabledSystemCategories: $includeSystemDisabledCategories) {
    ...CategoryFields
  }
}
"""
    + CATEGORY_GROUP_FIELDS
    + CATEGORY_FIELDS
)

GET_CATEGORY_GROUP_QUERY = (
    """
query GetCategoryGroup($id: UUID!) {
  categoryGroup(id: $id) {
    ...CategoryGroupFields
  }
}
"""
    + CATEGORY_GROUP_FIELDS
)

GET_CATEGORY_QUERY = (
    """
query Web_GetEditCategory($id: UUID!) {
  category(id: $id) {
    ...CategoryFields
  }
}
"""
    + CATEGORY_FIELDS
)

CREATE_CATEGORY_MUTATION = (
    """
mutation Web_CreateCategory($input: CreateCategoryInput!) {
  createCategory(input: $input) {
    errors {
      message
      code
    }
    category {
      ...CategoryFields
    }
  }
}
"""
    + CATEGORY_FIELDS
)

UPDATE_CATEGORY_MUTATION = (
    """
mutation Web_UpdateCategory($input: UpdateCategoryInput!) {
  updateCategory(input: $input) {
    errors {
      message
      code
    }
    category {
      ...CategoryFields
    }
  }
}
"""
    + CATEGORY_FIELDS
)

REMOVE_CATEGORY_MUTATION = """
mutation Web_DeleteCategory($id: UUID!, $moveToCategoryId: UUID) {
  deleteCategory(id: $id, moveToCategoryId: $moveToCategoryId) {
    errors {
      message
      code
    }
    deleted
  }
}
"""

REACTIVATE_CATEGORY_MUTATION = (
    """
mutation Web_RestoreCategory($id: UUID!) {
  restoreCategory(id: $id) {
    errors {
      message
      code
    }
    category {
      ...CategoryFields
    }
  }
}
"""
    + CATEGORY_FIELDS
)

REORDER_CATEGORY_MUTATION = (
    """
mutation Web_UpdateCategoryOrder($id: UUID!, $categoryGroupId: UUID!, $order: Int!) {
  updateCategoryOrderInCategoryGroup(
    id: $id
    categoryGroupId: $categoryGroupId
    order: $order
  ) {
    category {
      ...CategoryFields
    }
  }
}
"""
    + CATEGORY_FIELDS
)

CREATE_CATEGORY_GROUP_MUTATION = (
    """
mutation Common_CreateCategoryGroup($input: CreateCategoryGroupInput!) {
  createCategoryGroup(input: $input) {
    categoryGroup {
      ...CategoryGroupFields
    }
  }
}
"""
    + CATEGORY_GROUP_FIELDS
)

UPDATE_CATEGORY_GROUP_MUTATION = (
    """
mutation Common_UpdateCategoryGroup($input: UpdateCategoryGroupInput!) {
  updateCategoryGroup(input: $input) {
    categoryGroup {
      ...CategoryGroupFields
    }
  }
}
"""
    + CATEGORY_GROUP_FIELDS
)

DELETE_CATEGORY_GROUP_MUTATION = """
mutation Common_DeleteCategoryGroup($id: UUID!, $moveToGroupId: UUID) {
  deleteCategoryGroup(id: $id, moveToGroupId: $moveToGroupId) {
    deleted
    errors {
      message
      code
    }
  }
}
"""

REORDER_CATEGORY_GROUP_MUTATION = (
    """
mutation Web_UpdateCategoryGroupOrder($id: UUID!, $order: Int!) {
  updateCategoryGroupOrder(id: $id, order: $order) {
    categoryGroups {
      ...CategoryGroupFields
    }
  }
}
"""
    + CATEGORY_GROUP_FIELDS
)


def list_categories(
    session: AuthSession,
    *,
    filters: CategoryFilter | None = None,
    include_disabled: bool = False,
) -> list[Category]:
    data = graphql_request(
        session,
        "Common_GetCategories",
        LIST_CATEGORIES_QUERY,
        {"includeSystemDisabledCategories": include_disabled},
    )
    raw_categories = data.get("categories")
    categories = (
        [
            Category.from_api(category)
            for category in raw_categories
            if isinstance(category, dict)
        ]
        if isinstance(raw_categories, list)
        else []
    )
    if filters is None:
        return categories
    return [category for category in categories if filters.matches(category)]


def list_category_groups(session: AuthSession) -> list[CategoryGroup]:
    data = graphql_request(
        session,
        "Common_GetCategoryGroups",
        LIST_CATEGORY_GROUPS_QUERY,
        {},
    )
    raw_groups = data.get("categoryGroups")
    groups = raw_groups if isinstance(raw_groups, list) else []
    return [
        CategoryGroup.from_api(group)
        for group in groups
        if isinstance(group, dict)
    ]


def get_category_catalog(
    session: AuthSession,
    *,
    include_disabled: bool = False,
) -> CategoryCatalog:
    data = _category_data(session, include_disabled=include_disabled)
    groups = _sort_groups(data["category_groups"])
    categories = _sort_categories(data["categories"], groups)
    return CategoryCatalog(
        groups=[CategoryGroup.from_api(group) for group in groups],
        categories=categories,
    )


def get_category_group(session: AuthSession, group_id: str) -> CategoryGroup | None:
    data = graphql_request(
        session,
        "GetCategoryGroup",
        GET_CATEGORY_GROUP_QUERY,
        {"id": group_id},
    )
    group = data.get("categoryGroup")
    if not isinstance(group, dict):
        return None
    return CategoryGroup.from_api(group)


def get_category(session: AuthSession, category_id: str) -> Category | None:
    data = graphql_request(
        session,
        "Web_GetEditCategory",
        GET_CATEGORY_QUERY,
        {"id": category_id},
    )
    category = data.get("category")
    if not isinstance(category, dict):
        return None
    return Category.from_api(category)


def create_category(
    session: AuthSession,
    *,
    name: str,
    group_id: str,
    icon: str,
) -> Category:
    data = graphql_request(
        session,
        "Web_CreateCategory",
        CREATE_CATEGORY_MUTATION,
        {
            "input": {
                "name": name,
                "group": group_id,
                "icon": icon,
            }
        },
    )
    payload = _payload(data, "createCategory")
    _raise_payload_errors(payload)
    return _category_payload(payload, "created")


def update_category(
    session: AuthSession,
    category_id: str,
    *,
    name: str | None = None,
    group_id: str | None = None,
    icon: str | None = None,
) -> Category:
    data = graphql_request(
        session,
        "Web_UpdateCategory",
        UPDATE_CATEGORY_MUTATION,
        {
            "input": _clean(
                {
                    "id": category_id,
                    "name": name,
                    "group": group_id,
                    "icon": icon,
                }
            )
        },
    )
    payload = _payload(data, "updateCategory")
    _raise_payload_errors(payload)
    return _category_payload(payload, "updated")


def remove_category(
    session: AuthSession,
    category_id: str,
    *,
    move_to_category_id: str | None = None,
) -> bool:
    data = graphql_request(
        session,
        "Web_DeleteCategory",
        REMOVE_CATEGORY_MUTATION,
        {"id": category_id, "moveToCategoryId": move_to_category_id},
    )
    payload = _payload(data, "deleteCategory")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


def reactivate_category(session: AuthSession, category_id: str) -> Category:
    data = graphql_request(
        session,
        "Web_RestoreCategory",
        REACTIVATE_CATEGORY_MUTATION,
        {"id": category_id},
    )
    payload = _payload(data, "restoreCategory")
    _raise_payload_errors(payload)
    return _category_payload(payload, "reactivated")


def reorder_category(
    session: AuthSession,
    category_id: str,
    *,
    group_id: str,
    order: int,
) -> Category:
    data = graphql_request(
        session,
        "Web_UpdateCategoryOrder",
        REORDER_CATEGORY_MUTATION,
        {
            "id": category_id,
            "categoryGroupId": group_id,
            "order": order,
        },
    )
    payload = _payload(data, "updateCategoryOrderInCategoryGroup")
    return _category_payload(payload, "reordered")


def create_category_group(
    session: AuthSession,
    *,
    name: str,
    type: CategoryType,
) -> CategoryGroup:
    data = graphql_request(
        session,
        "Common_CreateCategoryGroup",
        CREATE_CATEGORY_GROUP_MUTATION,
        {"input": {"name": name, "type": type.value}},
    )
    payload = _payload(data, "createCategoryGroup")
    return _category_group_payload(payload, "created")


def update_category_group(
    session: AuthSession,
    group_id: str,
    *,
    name: str | None = None,
    type: CategoryType | None = None,
) -> CategoryGroup:
    data = graphql_request(
        session,
        "Common_UpdateCategoryGroup",
        UPDATE_CATEGORY_GROUP_MUTATION,
        {
            "input": _clean(
                {
                    "id": group_id,
                    "name": name,
                    "type": type.value if type is not None else None,
                }
            )
        },
    )
    payload = _payload(data, "updateCategoryGroup")
    return _category_group_payload(payload, "updated")


def delete_category_group(
    session: AuthSession,
    group_id: str,
    *,
    move_to_group_id: str | None = None,
) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteCategoryGroup",
        DELETE_CATEGORY_GROUP_MUTATION,
        {"id": group_id, "moveToGroupId": move_to_group_id},
    )
    payload = _payload(data, "deleteCategoryGroup")
    _raise_payload_errors(payload)
    return bool(payload.get("deleted"))


def reorder_category_group(
    session: AuthSession,
    group_id: str,
    *,
    order: int,
) -> list[CategoryGroup]:
    data = graphql_request(
        session,
        "Web_UpdateCategoryGroupOrder",
        REORDER_CATEGORY_GROUP_MUTATION,
        {"id": group_id, "order": order},
    )
    payload = _payload(data, "updateCategoryGroupOrder")
    groups = payload.get("categoryGroups")
    if not isinstance(groups, list):
        return []
    return [
        CategoryGroup.from_api(group)
        for group in _sort_groups(groups)
        if isinstance(group, dict)
    ]


def _category_data(
    session: AuthSession,
    *,
    include_disabled: bool,
) -> _CategoryData:
    data = graphql_request(
        session,
        "Common_GetCategories",
        GET_CATEGORY_CATALOG_QUERY,
        {"includeSystemDisabledCategories": include_disabled},
    )
    raw_categories = data.get("categories")
    raw_groups = data.get("categoryGroups")
    categories = (
        [
            Category.from_api(category)
            for category in raw_categories
            if isinstance(category, dict)
        ]
        if isinstance(raw_categories, list)
        else []
    )
    groups = (
        [group for group in raw_groups if isinstance(group, dict)]
        if isinstance(raw_groups, list)
        else []
    )
    return {"categories": categories, "category_groups": groups}


def _sort_groups(groups: list[JsonDict]) -> list[JsonDict]:
    return sorted(groups, key=_group_sort_key)


def _sort_categories(
    categories: list[Category],
    groups: list[JsonDict],
) -> list[Category]:
    group_order = {
        str(group["id"]): _sort_number(group.get("order"))
        for group in groups
        if group.get("id") is not None
    }
    return sorted(
        categories,
        key=lambda category: (
            group_order.get(
                category.group.id if category.group is not None else "",
                _SORT_LAST,
            ),
            _sort_number(category.order),
            category.name.casefold(),
            category.id,
        ),
    )


def _group_sort_key(group: JsonDict) -> tuple[int, str, str]:
    return (
        _sort_number(group.get("order")),
        str(group.get("name") or "").casefold(),
        str(group.get("id") or ""),
    )


_SORT_LAST = 1_000_000


def _sort_number(value: object) -> int:
    return value if isinstance(value, int) else _SORT_LAST


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    return payload


def _category_payload(payload: JsonDict, action: str) -> Category:
    category = payload.get("category")
    if not isinstance(category, dict):
        raise MonarchError(f"Monarch did not return the {action} category.")
    return Category.from_api(category)


def _category_group_payload(payload: JsonDict, action: str) -> CategoryGroup:
    category_group = payload.get("categoryGroup")
    if not isinstance(category_group, dict):
        raise MonarchError(f"Monarch did not return the {action} category group.")
    return CategoryGroup.from_api(category_group)


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


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}
