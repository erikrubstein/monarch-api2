from __future__ import annotations

from datetime import date

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.budget import (
    Budget,
    BudgetCategory,
    BudgetCategoryGroup,
    BudgetCategoryRow,
    BudgetFlexRow,
    BudgetGroupRow,
    BudgetRolloverFrequency,
    BudgetRolloverType,
    BudgetSettings,
    BudgetVariability,
    FlexRolloverSettings,
)
from monarch_api.types.categories import CategoryType
from monarch_api.types.common import JsonDict


BUDGET_FIELDS = """
fragment BudgetFields on BudgetData {
  monthlyAmountsByCategory {
    category {
      id
    }
    monthlyAmounts {
      month
      plannedAmount
      plannedCashFlowAmount
      plannedSetAsideAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
      rolloverType
      cumulativeActualAmount
      rolloverTargetAmount
    }
  }
  monthlyAmountsByCategoryGroup {
    categoryGroup {
      id
    }
    monthlyAmounts {
      month
      plannedAmount
      plannedCashFlowAmount
      plannedSetAsideAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
      rolloverType
      cumulativeActualAmount
      rolloverTargetAmount
    }
  }
  monthlyAmountsForFlexExpense {
    budgetVariability
    monthlyAmounts {
      month
      plannedAmount
      plannedCashFlowAmount
      plannedSetAsideAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
      rolloverType
      cumulativeActualAmount
      rolloverTargetAmount
    }
  }
  totalsByMonth {
    month
    totalIncome {
      plannedAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
    }
    totalExpenses {
      plannedAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
    }
    totalFixedExpenses {
      plannedAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
    }
    totalNonMonthlyExpenses {
      plannedAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
    }
    totalFlexibleExpenses {
      plannedAmount
      actualAmount
      remainingAmount
      previousMonthRolloverAmount
    }
  }
}
"""

BUDGET_CATEGORY_FIELDS = """
fragment BudgetCategoryFields on Category {
  id
  order
  name
  icon
  isSystemCategory
  excludeFromBudget
  budgetVariability
  updatedAt
  rolloverPeriod {
    id
    startMonth
    endMonth
    startingBalance
    frequency
    targetAmount
    type
  }
  group {
    id
    name
    type
    budgetVariability
    groupLevelBudgetingEnabled
  }
}
"""

BUDGET_CATEGORY_GROUP_FIELDS = (
    """
fragment BudgetCategoryGroupFields on CategoryGroup {
  id
  name
  order
  type
  budgetVariability
  groupLevelBudgetingEnabled
  updatedAt
  rolloverPeriod {
    id
    startMonth
    endMonth
    startingBalance
    frequency
    targetAmount
    type
  }
  categories {
    ...BudgetCategoryFields
  }
}
"""
    + BUDGET_CATEGORY_FIELDS
)

GET_BUDGET_QUERY = (
    """
query Common_BudgetDataQuery($startDate: Date!, $endDate: Date!) {
  budgetSystem
  budgetApplyToFutureMonthsDefault
  budgetStatus {
    hasBudget
    hasTransactions
    willCreateBudgetFromEmptyDefaultCategories
  }
  budgetData(startMonth: $startDate, endMonth: $endDate) {
    ...BudgetFields
  }
  categoryGroups {
    ...BudgetCategoryGroupFields
  }
}
"""
    + BUDGET_FIELDS
    + BUDGET_CATEGORY_GROUP_FIELDS
)

GET_BUDGET_SETTINGS_QUERY = """
query Common_BudgetSettings {
  budgetSystem
  budgetApplyToFutureMonthsDefault
  budgetStatus {
    hasBudget
    hasTransactions
    willCreateBudgetFromEmptyDefaultCategories
  }
  flexExpenseRolloverPeriod {
    id
    startMonth
    endMonth
    startingBalance
    frequency
    targetAmount
    type
  }
}
"""

GET_FLEX_ROLLOVER_SETTINGS_QUERY = """
query Web_GetFlexibleGroupRolloverSettings {
  budgetSystem
  flexExpenseRolloverPeriod {
    id
    startMonth
    endMonth
    startingBalance
    frequency
    targetAmount
    type
  }
}
"""

UPDATE_BUDGET_ITEM_MUTATION = """
mutation Common_UpdateBudgetItem($input: UpdateOrCreateBudgetItemMutationInput!) {
  updateOrCreateBudgetItem(input: $input) {
    budgetItem {
      id
      plannedCashFlowAmount
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_FLEX_BUDGET_MUTATION = """
mutation Common_UpdateFlexBudgetMutation(
  $input: UpdateOrCreateFlexBudgetItemMutationInput!
) {
  updateOrCreateFlexBudgetItem(input: $input) {
    budgetItem {
      id
      budgetAmount
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_CATEGORY_BUDGET_SETTINGS_MUTATION = (
    """
mutation Common_UpdateCategoryBudgetSettings($input: UpdateCategoryInput!) {
  updateCategory(input: $input) {
    category {
      ...BudgetCategoryFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + BUDGET_CATEGORY_FIELDS
)

UPDATE_CATEGORY_GROUP_BUDGET_SETTINGS_MUTATION = (
    """
mutation Common_UpdateCategoryGroupBudgetSettings($input: UpdateCategoryGroupInput!) {
  updateCategoryGroup(input: $input) {
    categoryGroup {
      ...BudgetCategoryGroupFields
    }
  }
}
"""
    + BUDGET_CATEGORY_GROUP_FIELDS
)

UPDATE_FLEX_ROLLOVER_SETTINGS_MUTATION = """
mutation Web_UpdateFlexibleGroupRolloverSettings(
  $input: UpdateBudgetSettingsMutationInput!
) {
  updateBudgetSettings(input: $input) {
    budgetRolloverPeriod {
      id
      startMonth
      endMonth
      startingBalance
      frequency
      targetAmount
      type
    }
  }
}
"""

CREATE_BUDGET_MUTATION = """
mutation Common_CreateBudgetForHousehold($input: CreateBudgetMutationInput!) {
  createBudget(input: $input) {
    errors {
      message
      code
    }
  }
}
"""

RESET_BUDGET_MUTATION = """
mutation Common_ResetBudget($input: ResetBudgetMutationInput!) {
  resetBudget(input: $input) {
    errors {
      message
      code
    }
  }
}
"""

CLEAR_BUDGET_MUTATION = """
mutation Web_ClearAllMutation($input: ClearBudgetMutationInput!) {
  clearBudget(input: $input) {
    errors {
      message
      code
    }
  }
}
"""

RESET_BUDGET_ROLLOVER_MUTATION = """
mutation Web_ResetRolloverMutation($input: ResetBudgetRolloverInput!) {
  resetBudgetRollover(input: $input) {
    errors {
      message
      code
    }
  }
}
"""


def get_budget(session: AuthSession, month: str | date) -> Budget:
    budget_month = _month_value(month)
    data = _get_budget_data(session, budget_month, budget_month)
    return Budget.from_api(data, start_month=budget_month, end_month=budget_month)


def list_budget_months(
    session: AuthSession,
    start_month: str | date,
    end_month: str | date,
) -> list[Budget]:
    start = _month_value(start_month)
    end = _month_value(end_month)
    data = _get_budget_data(session, start, end)
    return [
        Budget.from_api(data, start_month=month, end_month=month)
        for month in _month_range(start, end)
    ]


def get_budget_settings(session: AuthSession) -> BudgetSettings:
    data = graphql_request(
        session,
        "Common_BudgetSettings",
        GET_BUDGET_SETTINGS_QUERY,
    )
    return BudgetSettings.from_api(data)


def get_budget_category(
    session: AuthSession,
    month: str | date,
    category_id: str,
) -> BudgetCategoryRow | None:
    budget = get_budget(session, month)
    return next(
        (row for row in budget.categories if row.category.id == str(category_id)),
        None,
    )


def get_flex_rollover_settings(session: AuthSession) -> FlexRolloverSettings:
    data = graphql_request(
        session,
        "Web_GetFlexibleGroupRolloverSettings",
        GET_FLEX_ROLLOVER_SETTINGS_QUERY,
    )
    return FlexRolloverSettings.from_api(data)


def set_budget_amount(
    session: AuthSession,
    month: str | date,
    category_id: str,
    amount: float,
    *,
    apply_to_future: bool = False,
    default_amount: float | None = None,
) -> BudgetCategoryRow:
    budget_month = _month_value(month)
    _update_budget_item(
        session,
        {
            "startDate": budget_month,
            "timeframe": "month",
            "categoryId": str(category_id),
            "amount": amount,
            "applyToFuture": apply_to_future,
            "defaultAmount": default_amount,
        },
    )
    row = get_budget_category(session, budget_month, category_id)
    if row is None:
        raise MonarchError("Budget category was not returned after update.")
    return row


def set_budget_group_amount(
    session: AuthSession,
    month: str | date,
    category_group_id: str,
    amount: float,
    *,
    apply_to_future: bool = False,
    default_amount: float | None = None,
) -> BudgetGroupRow:
    budget_month = _month_value(month)
    _update_budget_item(
        session,
        {
            "startDate": budget_month,
            "timeframe": "month",
            "categoryGroupId": str(category_group_id),
            "amount": amount,
            "applyToFuture": apply_to_future,
            "defaultAmount": default_amount,
        },
    )
    budget = get_budget(session, budget_month)
    row = next(
        (row for row in budget.groups if row.group.id == str(category_group_id)),
        None,
    )
    if row is None:
        raise MonarchError("Budget group was not returned after update.")
    return row


def set_flex_budget_amount(
    session: AuthSession,
    month: str | date,
    amount: float,
    *,
    apply_to_future: bool = False,
    default_amount: float | None = None,
) -> BudgetFlexRow:
    budget_month = _month_value(month)
    data = graphql_request(
        session,
        "Common_UpdateFlexBudgetMutation",
        UPDATE_FLEX_BUDGET_MUTATION,
        {
            "input": _clean(
                {
                    "startDate": budget_month,
                    "amount": amount,
                    "applyToFuture": apply_to_future,
                    "defaultAmount": default_amount,
                }
            )
        },
    )
    _payload(data, "updateOrCreateFlexBudgetItem")
    budget = get_budget(session, budget_month)
    if budget.flex is None:
        raise MonarchError("Flex budget row was not returned after update.")
    return budget.flex


def set_budget_category_variability(
    session: AuthSession,
    category_id: str,
    variability: BudgetVariability | str,
) -> BudgetCategory:
    category = _update_category_budget_settings(
        session,
        {
            "id": str(category_id),
            "budgetVariability": _enum_value(variability),
        },
    )
    parsed = BudgetCategory.from_api(category)
    if parsed is None:
        raise MonarchError("Budget category was not returned after update.")
    return parsed


def set_budget_group_variability(
    session: AuthSession,
    category_group_id: str,
    variability: BudgetVariability | str,
) -> BudgetCategoryGroup:
    group = _update_category_group_budget_settings(
        session,
        {
            "id": str(category_group_id),
            "budgetVariability": _enum_value(variability),
        },
    )
    parsed = BudgetCategoryGroup.from_api(group)
    if parsed is None:
        raise MonarchError("Budget category group was not returned after update.")
    return parsed


def set_budget_category_rollover(
    session: AuthSession,
    category_id: str,
    *,
    enabled: bool,
    start_month: str | date | None = None,
    starting_balance: float | None = None,
    frequency: BudgetRolloverFrequency | str | None = None,
    target_amount: float | None = None,
    rollover_type: BudgetRolloverType | str | None = None,
    apply_to_future: bool | None = None,
) -> BudgetCategory:
    category = _update_category_budget_settings(
        session,
        {
            "id": str(category_id),
            "rolloverEnabled": enabled,
            "rolloverStartMonth": (
                _month_value(start_month) if start_month is not None else None
            ),
            "rolloverStartingBalance": starting_balance,
            "rolloverFrequency": _enum_value(frequency),
            "rolloverTargetAmount": target_amount,
            "rolloverType": _enum_value(rollover_type),
            "applyRolloverBudgetToFutureMonths": apply_to_future,
        },
    )
    parsed = BudgetCategory.from_api(category)
    if parsed is None:
        raise MonarchError("Budget category was not returned after update.")
    return parsed


def set_budget_group_rollover(
    session: AuthSession,
    category_group_id: str,
    *,
    enabled: bool,
    start_month: str | date | None = None,
    starting_balance: float | None = None,
    rollover_type: BudgetRolloverType | str | None = None,
) -> BudgetCategoryGroup:
    group = _update_category_group_budget_settings(
        session,
        {
            "id": str(category_group_id),
            "rolloverEnabled": enabled,
            "rolloverStartMonth": (
                _month_value(start_month) if start_month is not None else None
            ),
            "rolloverStartingBalance": starting_balance,
            "rolloverType": _enum_value(rollover_type),
        },
    )
    parsed = BudgetCategoryGroup.from_api(group)
    if parsed is None:
        raise MonarchError("Budget category group was not returned after update.")
    return parsed


def set_flex_rollover_settings(
    session: AuthSession,
    *,
    enabled: bool,
    start_month: str | date | None = None,
    starting_balance: float | None = None,
) -> FlexRolloverSettings:
    data = graphql_request(
        session,
        "Web_UpdateFlexibleGroupRolloverSettings",
        UPDATE_FLEX_ROLLOVER_SETTINGS_MUTATION,
        {
            "input": _clean(
                {
                    "rolloverEnabled": enabled,
                    "rolloverStartMonth": (
                        _month_value(start_month) if start_month is not None else None
                    ),
                    "rolloverStartingBalance": starting_balance,
                }
            )
        },
    )
    _payload(data, "updateBudgetSettings")
    return get_flex_rollover_settings(session)


def reset_budget_rollover(
    session: AuthSession,
    month: str | date,
    *,
    category_id: str | None = None,
    category_group_id: str | None = None,
    starting_balance: float | None = None,
) -> Budget:
    if (category_id is None) == (category_group_id is None):
        raise ValueError("Pass exactly one of category_id or category_group_id.")

    budget_month = _month_value(month)
    data = graphql_request(
        session,
        "Web_ResetRolloverMutation",
        RESET_BUDGET_ROLLOVER_MUTATION,
        {
            "input": _clean(
                {
                    "categoryId": category_id,
                    "categoryGroupId": category_group_id,
                    "startMonth": budget_month,
                    "startingBalance": starting_balance,
                }
            )
        },
    )
    _payload(data, "resetBudgetRollover")
    return get_budget(session, budget_month)


def create_budget(
    session: AuthSession,
    month: str | date,
) -> Budget:
    budget_month = _month_value(month)
    data = graphql_request(
        session,
        "Common_CreateBudgetForHousehold",
        CREATE_BUDGET_MUTATION,
        {"input": {"startDate": budget_month, "timeframe": "month"}},
    )
    _payload(data, "createBudget")
    return get_budget(session, budget_month)


def reset_budget(
    session: AuthSession,
    month: str | date,
    *,
    category_ids: list[str] | None = None,
    category_type: CategoryType | str | None = None,
    budget_variability: BudgetVariability | str | None = None,
    overwrite_existing: bool = False,
) -> Budget:
    budget_month = _month_value(month)
    filters = _clean(
        {
            "categoryIds": category_ids,
            "categoryType": _enum_value(category_type),
            "budgetVariability": _enum_value(budget_variability),
        }
    )
    data = graphql_request(
        session,
        "Common_ResetBudget",
        RESET_BUDGET_MUTATION,
        {
            "input": _clean(
                {
                    "startDate": budget_month,
                    "overwriteExisting": overwrite_existing,
                    "filters": filters or None,
                }
            )
        },
    )
    _payload(data, "resetBudget")
    return get_budget(session, budget_month)


def clear_budget(
    session: AuthSession,
    month: str | date,
    *,
    confirm: bool = False,
) -> Budget:
    if not confirm:
        raise ValueError("Pass confirm=True to clear budget amounts for the month.")

    budget_month = _month_value(month)
    data = graphql_request(
        session,
        "Web_ClearAllMutation",
        CLEAR_BUDGET_MUTATION,
        {"input": {"startDate": budget_month}},
    )
    _payload(data, "clearBudget")
    return get_budget(session, budget_month)


def _get_budget_data(
    session: AuthSession,
    start_month: str,
    end_month: str,
) -> JsonDict:
    return graphql_request(
        session,
        "Common_BudgetDataQuery",
        GET_BUDGET_QUERY,
        {"startDate": start_month, "endDate": end_month},
    )


def _update_budget_item(session: AuthSession, input_data: JsonDict) -> None:
    data = graphql_request(
        session,
        "Common_UpdateBudgetItem",
        UPDATE_BUDGET_ITEM_MUTATION,
        {"input": _clean(input_data)},
    )
    _payload(data, "updateOrCreateBudgetItem")


def _update_category_budget_settings(
    session: AuthSession,
    input_data: JsonDict,
) -> JsonDict:
    data = graphql_request(
        session,
        "Common_UpdateCategoryBudgetSettings",
        UPDATE_CATEGORY_BUDGET_SETTINGS_MUTATION,
        {"input": _clean(input_data)},
    )
    payload = _payload(data, "updateCategory")
    category = payload.get("category")
    return category if isinstance(category, dict) else {}


def _update_category_group_budget_settings(
    session: AuthSession,
    input_data: JsonDict,
) -> JsonDict:
    data = graphql_request(
        session,
        "Common_UpdateCategoryGroupBudgetSettings",
        UPDATE_CATEGORY_GROUP_BUDGET_SETTINGS_MUTATION,
        {"input": _clean(input_data)},
    )
    payload = data.get("updateCategoryGroup")
    if not isinstance(payload, dict):
        raise MonarchError("Monarch did not return updateCategoryGroup.")
    group = payload.get("categoryGroup")
    return group if isinstance(group, dict) else {}


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch did not return {key}.")

    errors = payload.get("errors")
    if errors:
        raise MonarchError(str(errors))
    return payload


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _month_value(value: str | date) -> str:
    if isinstance(value, date):
        return value.replace(day=1).isoformat()

    text = str(value)
    if len(text) == 7:
        text = f"{text}-01"
    try:
        return date.fromisoformat(text[:10]).replace(day=1).isoformat()
    except ValueError as exc:
        raise ValueError("Budget month must be YYYY-MM or YYYY-MM-DD.") from exc


def _month_range(start_month: str, end_month: str) -> list[str]:
    start = date.fromisoformat(start_month)
    end = date.fromisoformat(end_month)
    if start > end:
        raise ValueError("start_month must be before or equal to end_month.")

    months: list[str] = []
    cursor = start
    while cursor <= end:
        months.append(cursor.isoformat())
        cursor = _add_month(cursor)
    return months


def _add_month(value: date) -> date:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    return date(year, month, 1)
