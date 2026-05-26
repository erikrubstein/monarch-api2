from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import (
    AccountReference,
    GoalReference,
    Transaction,
)


class GoalType(str, Enum):
    CUSTOM = "custom"
    SAVINGS = "savings"
    DEBT = "debt"
    ASSET = "asset"
    EMERGENCY_FUND = "emergency_fund"
    HOME = "home"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    VEHICLE = "vehicle"
    VACATION = "vacation"
    LARGE_PURCHASE = "large_purchase"


class GoalStatus(str, Enum):
    AHEAD = "ahead"
    ARCHIVED = "archived"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    ON_TRACK = "on_track"


class GoalEventType(str, Enum):
    CONTRIBUTION = "contribution"
    MIGRATION = "migration"
    PRICE_CHANGE = "price_change"
    REBALANCE = "rebalance"
    SPENDING = "spending"
    TRANSACTION_ADJUSTMENT = "transaction_adjustment"
    WITHDRAWAL = "withdrawal"


@dataclass(slots=True)
class GoalAllocationSummary:
    goal_id: str
    account: AccountReference | None = None
    adjustment_amount: float | None = None
    total_amount: float | None = None
    spending_amount: float | None = None
    contributions_amount: float | None = None
    withdrawals_amount: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> GoalAllocationSummary:
        return cls(
            goal_id=str(data.get("goalId") or ""),
            account=AccountReference.from_api(_dict(data.get("account"))),
            adjustment_amount=_float(data.get("adjustmentAmount")),
            total_amount=_float(data.get("totalAmount")),
            spending_amount=_float(data.get("spendingAmount")),
            contributions_amount=_float(data.get("contributionsAmount")),
            withdrawals_amount=_float(data.get("withdrawalsAmount")),
            raw=dict(data),
        )


@dataclass(slots=True)
class GoalAccountBalanceLink:
    id: str
    account: AccountReference | None = None
    amount: float | None = None
    current_amount: float | None = None
    use_entire_balance: bool | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> GoalAccountBalanceLink:
        return cls(
            id=str(data.get("id") or ""),
            account=AccountReference.from_api(_dict(data.get("account"))),
            amount=_float(data.get("amount")),
            current_amount=_float(data.get("currentAmount")),
            use_entire_balance=data.get("useEntireAccountBalance"),
            raw=dict(data),
        )


@dataclass(slots=True)
class Goal:
    id: str
    name: str
    type: GoalType | None = None
    status: GoalStatus | None = None
    created_at: str | None = None
    archived_at: str | None = None
    completed_at: str | None = None
    image_storage_provider: str | None = None
    image_storage_provider_id: str | None = None
    progress: float | None = None
    current_balance: float | None = None
    target_date: str | None = None
    target_amount: float | None = None
    has_future_budget_different_from_current_month: bool | None = None
    current_month_actual_budget_amount: float | None = None
    current_month_planned_contribution_amount: float | None = None
    planned_monthly_contribution: float | None = None
    spending_total: float | None = None
    net_contribution: float | None = None
    net_contribution_with_spending: float | None = None
    net_contribution_without_spending: float | None = None
    balance_this_month: float | None = None
    estimated_months_until_completion: int | None = None
    forecasted_completion_date: str | None = None
    is_sinking_fund: bool | None = None
    priority: int | None = None
    allocation_summaries: list[GoalAllocationSummary] = field(default_factory=list)
    account_balance_links: list[GoalAccountBalanceLink] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Goal:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            type=_goal_type(data.get("type")),
            status=_goal_status(data.get("status")),
            created_at=data.get("createdAt"),
            archived_at=data.get("archivedAt"),
            completed_at=data.get("completedAt"),
            image_storage_provider=data.get("imageStorageProvider"),
            image_storage_provider_id=data.get("imageStorageProviderId"),
            progress=_float(data.get("progress")),
            current_balance=_float(data.get("currentBalance")),
            target_date=data.get("targetDate"),
            target_amount=_float(data.get("targetAmount")),
            has_future_budget_different_from_current_month=data.get(
                "hasFutureBudgetDifferentFromCurrentMonth"
            ),
            current_month_actual_budget_amount=_float(
                data.get("currentMonthActualBudgetAmount")
            ),
            current_month_planned_contribution_amount=_float(
                data.get("currentMonthPlannedContributionAmount")
            ),
            planned_monthly_contribution=_float(
                data.get("plannedMonthlyContribution")
            ),
            spending_total=_float(data.get("spendingTotal")),
            net_contribution=_float(data.get("netContribution")),
            net_contribution_with_spending=_float(
                data.get("netContributionWithSpending")
            ),
            net_contribution_without_spending=_float(
                data.get("netContributionWithoutSpending")
            ),
            balance_this_month=_float(data.get("balanceThisMonth")),
            estimated_months_until_completion=_int(
                data.get("estimatedMonthsUntilCompletion")
            ),
            forecasted_completion_date=data.get("forecastedCompletionDate"),
            is_sinking_fund=data.get("isSinkingFund"),
            priority=_int(data.get("priority")),
            allocation_summaries=[
                GoalAllocationSummary.from_api(allocation)
                for allocation in data.get("allocationAmountsByAccount") or []
                if isinstance(allocation, dict)
            ],
            account_balance_links=_goal_account_balance_links(data),
            raw=dict(data),
        )


@dataclass(slots=True)
class GoalEvent:
    id: str
    date: str
    amount: float
    type: GoalEventType | None = None
    created_at: str | None = None
    can_delete: bool | None = None
    include_in_budget: bool | None = None
    notes: str | None = None
    account: AccountReference | None = None
    goal: GoalReference | None = None
    transaction: Transaction | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> GoalEvent:
        transaction = data.get("transaction")
        return cls(
            id=str(data["id"]),
            date=str(data.get("date") or ""),
            amount=_float(data.get("amount")) or 0.0,
            type=_goal_event_type(data.get("type")),
            created_at=data.get("createdAt"),
            can_delete=data.get("canDelete"),
            include_in_budget=data.get("includeInBudget"),
            notes=data.get("notes"),
            account=AccountReference.from_api(_dict(data.get("account"))),
            goal=GoalReference.from_api(_dict(data.get("goal"))),
            transaction=(
                Transaction.from_api(transaction)
                if isinstance(transaction, dict)
                else None
            ),
            raw=dict(data),
        )


@dataclass(slots=True)
class GoalBudgetAmount:
    id: str
    month: str
    planned_amount: float | None = None
    actual_amount: float | None = None
    remaining_amount: float | None = None
    total_planned_amount: float | None = None
    total_actual_amount: float | None = None
    total_remaining_amount: float | None = None
    account_breakdown: list[JsonDict] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> GoalBudgetAmount:
        return cls(
            id=str(data["id"]),
            month=str(data.get("month") or ""),
            planned_amount=_float(data.get("plannedAmount")),
            actual_amount=_float(data.get("actualAmount")),
            remaining_amount=_float(data.get("remainingAmount")),
            total_planned_amount=_float(data.get("totalPlannedAmount")),
            total_actual_amount=_float(data.get("totalActualAmount")),
            total_remaining_amount=_float(data.get("totalRemainingAmount")),
            account_breakdown=[
                dict(row)
                for row in data.get("accountBreakdown") or []
                if isinstance(row, dict)
            ],
            raw=dict(data),
        )


def _goal_account_balance_links(data: JsonDict) -> list[GoalAccountBalanceLink]:
    links: list[GoalAccountBalanceLink] = []
    totals_by_account_id = {
        str(_dict(allocation.get("account")).get("id")): _float(
            allocation.get("totalAmount")
        )
        for allocation in data.get("allocationAmountsByAccount") or []
        if isinstance(allocation, dict)
        and _dict(allocation.get("account")).get("id") is not None
    }
    for account in data.get("linkedAccounts") or []:
        if not isinstance(account, dict):
            continue
        account_id = str(account.get("id") or "")
        links.append(
            GoalAccountBalanceLink(
                id=account_id,
                account=AccountReference.from_api(account),
                current_amount=totals_by_account_id.get(account_id),
                use_entire_balance=(
                    _dict(account.get("linkedGoal")).get("id") == data.get("id")
                ),
                raw=dict(account),
            )
        )
    return links


def _goal_type(value: object) -> GoalType | None:
    if not isinstance(value, str):
        return None
    try:
        return GoalType(value)
    except ValueError:
        return None


def _goal_status(value: object) -> GoalStatus | None:
    if not isinstance(value, str):
        return None
    try:
        return GoalStatus(value)
    except ValueError:
        return None


def _goal_event_type(value: object) -> GoalEventType | None:
    if not isinstance(value, str):
        return None
    try:
        return GoalEventType(value)
    except ValueError:
        return None


def _dict(value: object) -> JsonDict:
    if isinstance(value, dict):
        return value
    return {}


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
