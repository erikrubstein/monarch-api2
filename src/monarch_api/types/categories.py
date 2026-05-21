from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from monarch_api.types.common import JsonDict


class CategoryType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


def _category_type(value: object) -> CategoryType | None:
    if value is None:
        return None
    try:
        return CategoryType(str(value))
    except ValueError:
        return None


@dataclass(slots=True)
class CategoryGroupReference:
    id: str
    name: str | None = None
    type: CategoryType | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> CategoryGroupReference | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            type=_category_type(data.get("type")),
            raw=dict(data),
        )


@dataclass(slots=True)
class Category:
    id: str
    name: str
    icon: str | None = None
    order: int | None = None
    group: CategoryGroupReference | None = None
    type: CategoryType | None = None
    system_category: str | None = None
    system_category_display_name: str | None = None
    is_system: bool | None = None
    is_disabled: bool | None = None
    is_protected: bool | None = None
    exclude_from_budget: bool | None = None
    budget_variability: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Category:
        group = CategoryGroupReference.from_api(data.get("group"))
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            icon=data.get("icon"),
            order=data.get("order"),
            group=group,
            type=group.type if group is not None else None,
            system_category=data.get("systemCategory"),
            system_category_display_name=data.get("systemCategoryDisplayName"),
            is_system=data.get("isSystemCategory"),
            is_disabled=data.get("isDisabled"),
            is_protected=data.get("isProtected"),
            exclude_from_budget=data.get("excludeFromBudget"),
            budget_variability=data.get("budgetVariability"),
            raw=dict(data),
        )


@dataclass(slots=True)
class CategoryGroup:
    id: str
    name: str
    type: CategoryType | None = None
    order: int | None = None
    color: str | None = None
    group_level_budgeting_enabled: bool | None = None
    budget_variability: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> CategoryGroup:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            type=_category_type(data.get("type")),
            order=data.get("order"),
            color=data.get("color"),
            group_level_budgeting_enabled=data.get("groupLevelBudgetingEnabled"),
            budget_variability=data.get("budgetVariability"),
            raw=dict(data),
        )


@dataclass(slots=True)
class CategoryCatalog:
    groups: list[CategoryGroup]
    categories: list[Category]


@dataclass(slots=True)
class CategoryFilter:
    group_ids: list[str] | None = None
    types: list[CategoryType] | None = None

    def matches(self, category: Category) -> bool:
        if self.group_ids is not None:
            group_id = category.group.id if category.group is not None else None
            if group_id not in self.group_ids:
                return False
        if self.types is not None:
            allowed_types = {type_.value for type_ in self.types}
            if category.type is None or category.type.value not in allowed_types:
                return False
        return True
