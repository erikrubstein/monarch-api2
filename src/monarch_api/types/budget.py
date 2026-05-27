from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monarch_api.types.categories import CategoryType, _category_type
from monarch_api.types.common import JsonDict


class BudgetSystem(str, Enum):
    GROUPS_AND_CATEGORIES = "groups_and_categories"
    FIXED_AND_FLEX = "fixed_and_flex"


class BudgetVariability(str, Enum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"
    NON_MONTHLY = "non_monthly"


class BudgetRolloverFrequency(str, Enum):
    MONTHLY = "monthly"
    VARIABLE = "variable"
    EVERY_2_MONTHS = "every_2_months"
    EVERY_3_MONTHS = "every_3_months"
    EVERY_4_MONTHS = "every_4_months"
    EVERY_5_MONTHS = "every_5_months"
    EVERY_6_MONTHS = "every_6_months"
    EVERY_7_MONTHS = "every_7_months"
    EVERY_8_MONTHS = "every_8_months"
    EVERY_9_MONTHS = "every_9_months"
    EVERY_10_MONTHS = "every_10_months"
    EVERY_11_MONTHS = "every_11_months"
    EVERY_12_MONTHS = "every_12_months"


class BudgetRolloverType(str, Enum):
    MONTHLY = "monthly"
    NON_MONTHLY = "non_monthly"
    ONE_TIME = "one_time"


@dataclass(slots=True)
class BudgetStatus:
    has_budget: bool
    has_transactions: bool
    will_create_budget_from_empty_default_categories: bool
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetStatus | None:
        if not data:
            return None
        return cls(
            has_budget=bool(data.get("hasBudget")),
            has_transactions=bool(data.get("hasTransactions")),
            will_create_budget_from_empty_default_categories=bool(
                data.get("willCreateBudgetFromEmptyDefaultCategories")
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetAmount:
    month: str
    planned_amount: float | None = None
    planned_cash_flow_amount: float | None = None
    planned_set_aside_amount: float | None = None
    actual_amount: float | None = None
    remaining_amount: float | None = None
    previous_month_rollover_amount: float | None = None
    rollover_type: str | None = None
    cumulative_actual_amount: float | None = None
    rollover_target_amount: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> BudgetAmount:
        return cls(
            month=str(data["month"]),
            planned_amount=_float(data.get("plannedAmount")),
            planned_cash_flow_amount=_float(data.get("plannedCashFlowAmount")),
            planned_set_aside_amount=_float(data.get("plannedSetAsideAmount")),
            actual_amount=_float(data.get("actualAmount")),
            remaining_amount=_float(data.get("remainingAmount")),
            previous_month_rollover_amount=_float(
                data.get("previousMonthRolloverAmount")
            ),
            rollover_type=data.get("rolloverType"),
            cumulative_actual_amount=_float(data.get("cumulativeActualAmount")),
            rollover_target_amount=_float(data.get("rolloverTargetAmount")),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetTotals:
    planned_amount: float | None = None
    actual_amount: float | None = None
    remaining_amount: float | None = None
    previous_month_rollover_amount: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetTotals | None:
        if not data:
            return None
        return cls(
            planned_amount=_float(data.get("plannedAmount")),
            actual_amount=_float(data.get("actualAmount")),
            remaining_amount=_float(data.get("remainingAmount")),
            previous_month_rollover_amount=_float(
                data.get("previousMonthRolloverAmount")
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetMonthTotals:
    month: str
    income: BudgetTotals | None = None
    expenses: BudgetTotals | None = None
    fixed_expenses: BudgetTotals | None = None
    non_monthly_expenses: BudgetTotals | None = None
    flexible_expenses: BudgetTotals | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> BudgetMonthTotals:
        return cls(
            month=str(data["month"]),
            income=BudgetTotals.from_api(_dict(data.get("totalIncome"))),
            expenses=BudgetTotals.from_api(_dict(data.get("totalExpenses"))),
            fixed_expenses=BudgetTotals.from_api(
                _dict(data.get("totalFixedExpenses"))
            ),
            non_monthly_expenses=BudgetTotals.from_api(
                _dict(data.get("totalNonMonthlyExpenses"))
            ),
            flexible_expenses=BudgetTotals.from_api(
                _dict(data.get("totalFlexibleExpenses"))
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetRolloverPeriod:
    id: str
    start_month: str
    end_month: str | None = None
    starting_balance: float | None = None
    target_amount: float | None = None
    frequency: str | None = None
    type: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetRolloverPeriod | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            start_month=str(data.get("startMonth") or ""),
            end_month=data.get("endMonth"),
            starting_balance=_float(data.get("startingBalance")),
            target_amount=_float(data.get("targetAmount")),
            frequency=data.get("frequency"),
            type=data.get("type"),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetCategory:
    id: str
    name: str | None = None
    icon: str | None = None
    order: int | None = None
    type: CategoryType | None = None
    group_id: str | None = None
    group_type: CategoryType | None = None
    group_budget_variability: BudgetVariability | None = None
    group_level_budgeting_enabled: bool | None = None
    budget_variability: BudgetVariability | None = None
    exclude_from_budget: bool | None = None
    is_system: bool | None = None
    updated_at: str | None = None
    rollover_period: BudgetRolloverPeriod | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetCategory | None:
        if not data:
            return None
        group = _dict(data.get("group"))
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            icon=data.get("icon"),
            order=_int(data.get("order")),
            type=_category_type(group.get("type")),
            group_id=str(group["id"]) if group.get("id") is not None else None,
            group_type=_category_type(group.get("type")),
            group_budget_variability=_budget_variability(
                group.get("budgetVariability")
            ),
            group_level_budgeting_enabled=group.get("groupLevelBudgetingEnabled"),
            budget_variability=_budget_variability(data.get("budgetVariability")),
            exclude_from_budget=data.get("excludeFromBudget"),
            is_system=data.get("isSystemCategory"),
            updated_at=data.get("updatedAt"),
            rollover_period=BudgetRolloverPeriod.from_api(
                _dict(data.get("rolloverPeriod"))
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetCategoryGroup:
    id: str
    name: str | None = None
    type: CategoryType | None = None
    order: int | None = None
    budget_variability: BudgetVariability | None = None
    group_level_budgeting_enabled: bool | None = None
    updated_at: str | None = None
    rollover_period: BudgetRolloverPeriod | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetCategoryGroup | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            type=_category_type(data.get("type")),
            order=_int(data.get("order")),
            budget_variability=_budget_variability(data.get("budgetVariability")),
            group_level_budgeting_enabled=data.get("groupLevelBudgetingEnabled"),
            updated_at=data.get("updatedAt"),
            rollover_period=BudgetRolloverPeriod.from_api(
                _dict(data.get("rolloverPeriod"))
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetCategoryRow:
    category: BudgetCategory
    amounts: list[BudgetAmount] = field(default_factory=list)
    raw: JsonDict | None = None

    @property
    def amount(self) -> BudgetAmount | None:
        return self.amounts[0] if self.amounts else None


@dataclass(slots=True)
class BudgetGroupRow:
    group: BudgetCategoryGroup
    amounts: list[BudgetAmount] = field(default_factory=list)
    categories: list[BudgetCategoryRow] = field(default_factory=list)
    raw: JsonDict | None = None

    @property
    def amount(self) -> BudgetAmount | None:
        return self.amounts[0] if self.amounts else None


@dataclass(slots=True)
class BudgetFlexRow:
    budget_variability: BudgetVariability | None = None
    amounts: list[BudgetAmount] = field(default_factory=list)
    raw: JsonDict | None = None

    @property
    def amount(self) -> BudgetAmount | None:
        return self.amounts[0] if self.amounts else None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> BudgetFlexRow | None:
        if not data:
            return None
        return cls(
            budget_variability=_budget_variability(data.get("budgetVariability")),
            amounts=[
                BudgetAmount.from_api(amount)
                for amount in data.get("monthlyAmounts") or []
                if isinstance(amount, dict)
            ],
            raw=dict(data),
        )


@dataclass(slots=True)
class BudgetSettings:
    budget_system: BudgetSystem | None = None
    apply_to_future_months_default: bool | None = None
    status: BudgetStatus | None = None
    flex_rollover: BudgetRolloverPeriod | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> BudgetSettings:
        return cls(
            budget_system=_budget_system(data.get("budgetSystem")),
            apply_to_future_months_default=data.get(
                "budgetApplyToFutureMonthsDefault"
            ),
            status=BudgetStatus.from_api(_dict(data.get("budgetStatus"))),
            flex_rollover=BudgetRolloverPeriod.from_api(
                _dict(data.get("flexExpenseRolloverPeriod"))
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class FlexRolloverSettings:
    budget_system: BudgetSystem | None = None
    rollover_period: BudgetRolloverPeriod | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> FlexRolloverSettings:
        return cls(
            budget_system=_budget_system(data.get("budgetSystem")),
            rollover_period=BudgetRolloverPeriod.from_api(
                _dict(data.get("flexExpenseRolloverPeriod"))
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class Budget:
    start_month: str
    end_month: str
    budget_system: BudgetSystem | None = None
    status: BudgetStatus | None = None
    totals_by_month: list[BudgetMonthTotals] = field(default_factory=list)
    groups: list[BudgetGroupRow] = field(default_factory=list)
    categories: list[BudgetCategoryRow] = field(default_factory=list)
    flex: BudgetFlexRow | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        start_month: str,
        end_month: str,
    ) -> Budget:
        category_groups = _category_groups(data.get("categoryGroups"))
        categories = _categories(data.get("categoryGroups"))
        budget_data = _dict(data.get("budgetData"))
        category_rows = _category_rows(
            budget_data.get("monthlyAmountsByCategory"),
            categories,
            start_month,
            end_month,
        )
        group_rows = _group_rows(
            budget_data.get("monthlyAmountsByCategoryGroup"),
            category_groups,
            category_rows,
            start_month,
            end_month,
        )
        return cls(
            start_month=start_month,
            end_month=end_month,
            budget_system=_budget_system(data.get("budgetSystem")),
            status=BudgetStatus.from_api(_dict(data.get("budgetStatus"))),
            totals_by_month=[
                BudgetMonthTotals.from_api(total)
                for total in budget_data.get("totalsByMonth") or []
                if isinstance(total, dict)
                and _in_month_range(total.get("month"), start_month, end_month)
            ],
            groups=group_rows,
            categories=category_rows,
            flex=_flex_row(
                budget_data.get("monthlyAmountsForFlexExpense"),
                start_month,
                end_month,
            ),
            raw=dict(data),
        )


def _category_groups(value: object) -> dict[str, BudgetCategoryGroup]:
    if not isinstance(value, list):
        return {}
    groups: dict[str, BudgetCategoryGroup] = {}
    for group in value:
        parsed = BudgetCategoryGroup.from_api(_dict(group))
        if parsed is not None:
            groups[parsed.id] = parsed
    return groups


def _categories(value: object) -> dict[str, BudgetCategory]:
    if not isinstance(value, list):
        return {}
    categories: dict[str, BudgetCategory] = {}
    for group in value:
        for category in _dict(group).get("categories") or []:
            parsed = BudgetCategory.from_api(_dict(category))
            if parsed is not None:
                categories[parsed.id] = parsed
    return categories


def _category_rows(
    value: object,
    categories: dict[str, BudgetCategory],
    start_month: str,
    end_month: str,
) -> list[BudgetCategoryRow]:
    if not isinstance(value, list):
        return []
    rows: list[BudgetCategoryRow] = []
    for row in value:
        data = _dict(row)
        category_id = str(_dict(data.get("category")).get("id") or "")
        category = categories.get(category_id) or BudgetCategory(id=category_id)
        rows.append(
            BudgetCategoryRow(
                category=category,
                amounts=[
                    BudgetAmount.from_api(amount)
                    for amount in data.get("monthlyAmounts") or []
                    if isinstance(amount, dict)
                    and _in_month_range(amount.get("month"), start_month, end_month)
                ],
                raw=dict(data),
            )
        )
    return rows


def _group_rows(
    value: object,
    groups: dict[str, BudgetCategoryGroup],
    category_rows: list[BudgetCategoryRow],
    start_month: str,
    end_month: str,
) -> list[BudgetGroupRow]:
    if not isinstance(value, list):
        return []
    rows: list[BudgetGroupRow] = []
    categories_by_group: dict[str, list[BudgetCategoryRow]] = {}
    for row in category_rows:
        group_id = row.category.group_id
        if group_id is not None:
            categories_by_group.setdefault(group_id, []).append(row)

    for row in value:
        data = _dict(row)
        group_id = str(_dict(data.get("categoryGroup")).get("id") or "")
        group = groups.get(group_id) or BudgetCategoryGroup(id=group_id)
        rows.append(
            BudgetGroupRow(
                group=group,
                amounts=[
                    BudgetAmount.from_api(amount)
                    for amount in data.get("monthlyAmounts") or []
                    if isinstance(amount, dict)
                    and _in_month_range(amount.get("month"), start_month, end_month)
                ],
                categories=categories_by_group.get(group_id, []),
                raw=dict(data),
            )
        )
    return rows


def _flex_row(
    value: object,
    start_month: str,
    end_month: str,
) -> BudgetFlexRow | None:
    if isinstance(value, list):
        value = value[0] if value else None
    row = BudgetFlexRow.from_api(_dict(value))
    if row is None:
        return None
    row.amounts = [
        amount
        for amount in row.amounts
        if _in_month_range(amount.month, start_month, end_month)
    ]
    return row


def _budget_system(value: object) -> BudgetSystem | None:
    if not isinstance(value, str):
        return None
    try:
        return BudgetSystem(value)
    except ValueError:
        return None


def _budget_variability(value: object) -> BudgetVariability | None:
    if not isinstance(value, str):
        return None
    try:
        return BudgetVariability(value)
    except ValueError:
        return None


def _dict(value: object) -> JsonDict:
    if isinstance(value, dict):
        return value
    return {}


def _in_month_range(value: object, start_month: str, end_month: str) -> bool:
    if value is None:
        return False
    month = str(value)[:10]
    return start_month <= month <= end_month


def _float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float | str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float | str):
        try:
            return int(value)
        except ValueError:
            return None
    return None
