from __future__ import annotations

from collections.abc import Sequence
from enum import Enum

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.goals import (
    Goal,
    GoalBudgetAmount,
    GoalEvent,
    GoalStatus,
    GoalType,
)


GOAL_ACCOUNT_FIELDS = """
fragment GoalAccountFields on Account {
  id
  displayName
  icon
  logoUrl
  availableBalanceForGoals
  availableBalanceForGoalsUnmemoized
  includeInGoalContributions
  linkedGoal {
    id
    name
  }
  subtype {
    name
    display
  }
}
"""

GOAL_FIELDS = (
    """
fragment GoalFields on SavingsGoal {
  id
  type
  name
  createdAt
  archivedAt
  completedAt
  imageStorageProvider
  imageStorageProviderId
  status
  progress
  currentBalance
  targetDate
  targetAmount
  hasFutureBudgetDifferentFromCurrentMonth
  currentMonthActualBudgetAmount
  currentMonthPlannedContributionAmount
  plannedMonthlyContribution
  spendingTotal
  netContribution
  netContributionWithSpending
  netContributionWithoutSpending
  balanceThisMonth
  estimatedMonthsUntilCompletion
  forecastedCompletionDate
  isSinkingFund
  priority
  allocationAmountsByAccount {
    goalId
    adjustmentAmount
    totalAmount
    spendingAmount
    contributionsAmount
    withdrawalsAmount
    account {
      id
      displayName
      icon
      logoUrl
    }
  }
  linkedAccounts {
    ...GoalAccountFields
  }
}
"""
    + GOAL_ACCOUNT_FIELDS
)

GOAL_EVENT_FIELDS = """
fragment GoalEventFields on GoalEvent {
  id
  date
  amount
  type
  createdAt
  canDelete
  includeInBudget
  notes
  goal {
    id
    name
  }
  account {
    id
    displayName
    icon
    logoUrl
  }
  transaction {
    id
    amount
    pending
    date
    hideFromReports
    hiddenByAccount
    plaidName
    notes
    isRecurring
    reviewStatus
    needsReview
    isSplitTransaction
    dataProviderDescription
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
  }
}
"""

LIST_GOALS_QUERY = (
    """
query Common_SavingsGoals {
  savingsGoals {
    ...GoalFields
  }
}
"""
    + GOAL_FIELDS
)

GET_GOAL_QUERY = (
    """
query Common_SavingsGoal($id: ID!) {
  savingsGoal(id: $id) {
    ...GoalFields
  }
}
"""
    + GOAL_FIELDS
)

CREATE_GOALS_MUTATION = """
mutation Common_CreateSavingsGoals($input: CreateSavingsGoalsInput!) {
  createSavingsGoals(input: $input) {
    savingsGoals {
      id
      type
    }
    errors {
      message
      code
    }
  }
}
"""

UPDATE_GOAL_MUTATION = (
    """
mutation Common_UpdateSavingsGoal($input: UpdateSavingsGoalInput!) {
  updateSavingsGoal(input: $input) {
    savingsGoal {
      ...GoalFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + GOAL_FIELDS
)

DELETE_GOAL_MUTATION = """
mutation Common_DeleteSavingsGoal($input: DeleteSavingsGoalInput!) {
  deleteSavingsGoal(input: $input) {
    success
    errors {
      message
      code
    }
  }
}
"""

ARCHIVE_GOAL_MUTATION = (
    """
mutation Common_ArchiveSavingsGoal($input: ArchiveSavingsGoalInput!) {
  archiveSavingsGoal(input: $input) {
    savingsGoal {
      ...GoalFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + GOAL_FIELDS
)

RESTORE_GOAL_MUTATION = (
    """
mutation Common_UnarchiveSavingsGoal($input: UnarchiveSavingsGoalInput!) {
  unarchiveSavingsGoal(input: $input) {
    savingsGoal {
      ...GoalFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + GOAL_FIELDS
)

UPDATE_GOAL_PRIORITIES_MUTATION = """
mutation Common_UpdateSavingsGoalsPriorities(
  $input: UpdateSavingsGoalsPrioritiesInput!
) {
  updateSavingsGoalsPriorities(input: $input) {
    goals {
      id
      priority
    }
    errors {
      message
      code
    }
  }
}
"""

LINK_GOAL_ACCOUNT_MUTATION = """
mutation Common_CreateSavingsGoalAccountInitialContributions(
  $input: GoalAccountInitialContributionInput!
) {
  createGoalAccountInitialContributions(input: $input) {
    userNotice
    goalAccountForInitialContribution {
      account {
        id
        linkedGoal {
          id
        }
      }
      contributedGoals {
        accountId
        amount
        goal {
          id
          currentBalance
          progress
          status
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

LIST_GOAL_EVENTS_QUERY = (
    """
query Common_SavingsGoalEvents($id: ID!) {
  savingsGoal(id: $id) {
    id
    goalEvents {
      ...GoalEventFields
    }
  }
}
"""
    + GOAL_EVENT_FIELDS
)

CREATE_GOAL_CONTRIBUTION_MUTATION = """
mutation Common_ContributeToSavingsGoal(
  $input: CreateSavingsGoalContributionInput!
) {
  createSavingsGoalContribution(input: $input) {
    userNotice
    goalEvent {
      id
    }
  }
}
"""

CREATE_GOAL_WITHDRAWAL_MUTATION = """
mutation Common_WithdrawFromSavingsGoal(
  $input: CreateSavingsGoalWithdrawalInput!
) {
  createSavingsGoalWithdrawal(input: $input) {
    goalEvent {
      id
    }
  }
}
"""

UPDATE_GOAL_EVENT_MUTATION = (
    """
mutation Common_UpdateSavingsGoalEvent($input: UpdateGoalEventInput!) {
  updateGoalEvent(input: $input) {
    goalEvent {
      ...GoalEventFields
    }
  }
}
"""
    + GOAL_EVENT_FIELDS
)

DELETE_GOAL_EVENT_MUTATION = """
mutation Common_DeleteSavingsGoalEvent($input: DeleteGoalEventInput!) {
  deleteGoalEvent(input: $input) {
    success
  }
}
"""

GET_GOAL_BUDGET_AMOUNTS_QUERY = """
query Common_SavingsGoalBudgetAmounts(
  $goalId: ID!
  $startMonth: Date!
  $endMonth: Date!
) {
  savingsGoal(id: $goalId) {
    id
    monthlyBudgetAmounts(startMonth: $startMonth, endMonth: $endMonth) {
      id
      month
      plannedAmount
      actualAmount
      remainingAmount
      totalPlannedAmount
      totalActualAmount
      totalRemainingAmount
      accountBreakdown {
        id
        plannedAmount
        actualAmount
        remainingAmount
        account {
          id
        }
      }
    }
  }
}
"""

SET_GOAL_BUDGET_AMOUNT_MUTATION = """
mutation Common_SetSavingsGoalBudgetAmount(
  $input: SetSavingsGoalBudgetAmountInput!
) {
  setSavingsGoalBudgetAmount(input: $input) {
    success
    errors {
      message
      code
    }
  }
}
"""


def list_goals(
    session: AuthSession,
    *,
    include_archived: bool = False,
) -> list[Goal]:
    data = graphql_request(session, "Common_SavingsGoals", LIST_GOALS_QUERY)
    goals = [
        Goal.from_api(goal)
        for goal in data.get("savingsGoals") or []
        if isinstance(goal, dict)
    ]
    if include_archived:
        return goals
    return [goal for goal in goals if goal.archived_at is None]


def get_goal(session: AuthSession, goal_id: str) -> Goal | None:
    data = graphql_request(
        session,
        "Common_SavingsGoal",
        GET_GOAL_QUERY,
        {"id": goal_id},
    )
    goal = data.get("savingsGoal")
    if not isinstance(goal, dict):
        return None
    return Goal.from_api(goal)


def create_goal(
    session: AuthSession,
    *,
    name: str,
    goal_type: GoalType | str = GoalType.CUSTOM,
    target_amount: float | None = None,
    target_date: str | None = None,
    planned_monthly_contribution: float | None = None,
    is_sinking_fund: bool | None = None,
    priority: int | None = None,
    image_storage_provider: str | None = None,
    image_storage_provider_id: str | None = None,
) -> Goal:
    data = graphql_request(
        session,
        "Common_CreateSavingsGoals",
        CREATE_GOALS_MUTATION,
        {
            "input": {
                "goals": [
                    _clean(
                        {
                            "name": name,
                            "type": _goal_type_value(goal_type),
                            "targetAmount": target_amount,
                            "targetDate": target_date,
                            "plannedMonthlyContribution": planned_monthly_contribution,
                            "isSinkingFund": is_sinking_fund,
                            "priority": priority,
                            "imageStorageProvider": image_storage_provider,
                            "imageStorageProviderId": image_storage_provider_id,
                        }
                    )
                ]
            }
        },
    )
    payload = _payload(data, "createSavingsGoals")
    raw_goals = payload.get("savingsGoals")
    if not isinstance(raw_goals, list) or not raw_goals:
        raise MonarchError("Monarch did not return the created goal.")
    raw_goal = raw_goals[0]
    if not isinstance(raw_goal, dict):
        raise MonarchError("Monarch returned an invalid created goal.")
    created_goal = get_goal(session, str(raw_goal.get("id") or ""))
    if created_goal is None:
        raise MonarchError("Monarch created the goal but did not return it.")
    return created_goal


def update_goal(
    session: AuthSession,
    goal_id: str,
    *,
    name: str | None = None,
    goal_type: GoalType | str | None = None,
    target_amount: float | None = None,
    target_date: str | None = None,
    planned_monthly_contribution: float | None = None,
    is_sinking_fund: bool | None = None,
    priority: int | None = None,
    image_storage_provider: str | None = None,
    image_storage_provider_id: str | None = None,
    status: GoalStatus | str | None = None,
) -> Goal:
    updated_goal: Goal | None = None
    input_data = _clean(
        {
            "id": goal_id,
            "name": name,
            "type": _goal_type_value(goal_type) if goal_type is not None else None,
            "targetAmount": target_amount,
            "targetDate": target_date,
            "budgetToApplyToFutureMonths": planned_monthly_contribution,
            "isSinkingFund": is_sinking_fund,
            "priority": priority,
            "imageStorageProvider": image_storage_provider,
            "imageStorageProviderId": image_storage_provider_id,
        }
    )
    if len(input_data) > 1:
        data = graphql_request(
            session,
            "Common_UpdateSavingsGoal",
            UPDATE_GOAL_MUTATION,
            {"input": input_data},
        )
        payload = _payload(data, "updateSavingsGoal")
        updated_goal = _goal_payload(payload, "updated")

    if status is not None:
        normalized_status = _status_value(status)
        if normalized_status == GoalStatus.ARCHIVED.value:
            updated_goal = archive_goal(session, goal_id)
        elif normalized_status != GoalStatus.COMPLETED.value:
            updated_goal = restore_goal(session, goal_id)
        else:
            raise MonarchError("SavingsGoal completion does not have a verified endpoint.")

    if updated_goal is None:
        current_goal = get_goal(session, goal_id)
        if current_goal is None:
            raise MonarchError(f"Goal {goal_id} was not found.")
        return current_goal
    return updated_goal


def delete_goal(session: AuthSession, goal_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteSavingsGoal",
        DELETE_GOAL_MUTATION,
        {"input": {"id": goal_id}},
    )
    payload = _payload(data, "deleteSavingsGoal")
    return bool(payload.get("success"))


def archive_goal(session: AuthSession, goal_id: str) -> Goal:
    data = graphql_request(
        session,
        "Common_ArchiveSavingsGoal",
        ARCHIVE_GOAL_MUTATION,
        {"input": {"id": goal_id}},
    )
    payload = _payload(data, "archiveSavingsGoal")
    return _goal_payload(payload, "archived")


def restore_goal(session: AuthSession, goal_id: str) -> Goal:
    data = graphql_request(
        session,
        "Common_UnarchiveSavingsGoal",
        RESTORE_GOAL_MUTATION,
        {"input": {"id": goal_id}},
    )
    payload = _payload(data, "unarchiveSavingsGoal")
    return _goal_payload(payload, "restored")


def update_goal_priorities(
    session: AuthSession,
    goal_ids: Sequence[str],
) -> list[Goal]:
    data = graphql_request(
        session,
        "Common_UpdateSavingsGoalsPriorities",
        UPDATE_GOAL_PRIORITIES_MUTATION,
        {
            "input": {
                "goals": [
                    {"id": goal_id, "priority": priority}
                    for priority, goal_id in enumerate(goal_ids)
                ]
            }
        },
    )
    payload = _payload(data, "updateSavingsGoalsPriorities")
    raw_goals = payload.get("goals")
    if not isinstance(raw_goals, list):
        raise MonarchError("Monarch did not return updated goal priorities.")

    priority_by_id = {
        str(goal.get("id")): goal.get("priority")
        for goal in raw_goals
        if isinstance(goal, dict) and goal.get("id") is not None
    }
    goals = list_goals(session, include_archived=True)
    ordered_goals = [goal for goal in goals if goal.id in priority_by_id]
    return sorted(
        ordered_goals,
        key=lambda goal: (
            priority_by_id.get(goal.id)
            if isinstance(priority_by_id.get(goal.id), int)
            else goal.priority or 0
        ),
    )


def link_goal_account_balance(
    session: AuthSession,
    goal_id: str,
    account_id: str,
    *,
    use_entire_balance: bool = True,
    amount: float | None = None,
) -> Goal:
    return _set_goal_account_contribution(
        session,
        goal_id,
        account_id,
        contribution_amount=amount,
        use_entire_balance=use_entire_balance,
    )


def unlink_goal_account(
    session: AuthSession,
    goal_id: str,
    account_id: str,
) -> Goal:
    return _set_goal_account_contribution(
        session,
        goal_id,
        account_id,
        contribution_amount=None,
        use_entire_balance=False,
    )


def list_goal_events(session: AuthSession, goal_id: str) -> list[GoalEvent]:
    data = graphql_request(
        session,
        "Common_SavingsGoalEvents",
        LIST_GOAL_EVENTS_QUERY,
        {"id": goal_id},
    )
    goal = data.get("savingsGoal")
    if not isinstance(goal, dict):
        return []
    return [
        GoalEvent.from_api(event)
        for event in goal.get("goalEvents") or []
        if isinstance(event, dict)
    ]


def contribute_to_goal(
    session: AuthSession,
    goal_id: str,
    account_id: str,
    *,
    amount: float,
    date: str | None = None,
    include_in_budget: bool | None = None,
    notes: str | None = None,
) -> GoalEvent:
    return _create_goal_event(
        session,
        goal_id,
        account_id,
        amount=amount,
        date=date,
        include_in_budget=include_in_budget,
        notes=notes,
        operation_name="Common_ContributeToSavingsGoal",
        mutation=CREATE_GOAL_CONTRIBUTION_MUTATION,
        payload_key="createSavingsGoalContribution",
    )


def withdraw_from_goal(
    session: AuthSession,
    goal_id: str,
    account_id: str,
    *,
    amount: float,
    date: str | None = None,
    include_in_budget: bool | None = None,
    notes: str | None = None,
) -> GoalEvent:
    return _create_goal_event(
        session,
        goal_id,
        account_id,
        amount=amount,
        date=date,
        include_in_budget=include_in_budget,
        notes=notes,
        operation_name="Common_WithdrawFromSavingsGoal",
        mutation=CREATE_GOAL_WITHDRAWAL_MUTATION,
        payload_key="createSavingsGoalWithdrawal",
    )


def update_goal_event(
    session: AuthSession,
    event_id: str,
    *,
    date: str | None = None,
    include_in_budget: bool | None = None,
    notes: str | None = None,
) -> GoalEvent:
    data = graphql_request(
        session,
        "Common_UpdateSavingsGoalEvent",
        UPDATE_GOAL_EVENT_MUTATION,
        {
            "input": _clean(
                {
                    "eventId": event_id,
                    "date": date,
                    "includeInBudget": include_in_budget,
                    "notes": notes,
                }
            )
        },
    )
    payload = _payload(data, "updateGoalEvent")
    return _goal_event_payload(payload, "updated")


def delete_goal_event(session: AuthSession, event_id: str) -> bool:
    data = graphql_request(
        session,
        "Common_DeleteSavingsGoalEvent",
        DELETE_GOAL_EVENT_MUTATION,
        {"input": {"eventId": event_id}},
    )
    payload = _payload(data, "deleteGoalEvent")
    return bool(payload.get("success"))


def get_goal_budget_amounts(
    session: AuthSession,
    goal_id: str,
    start_month: str,
    end_month: str,
) -> list[GoalBudgetAmount]:
    data = graphql_request(
        session,
        "Common_SavingsGoalBudgetAmounts",
        GET_GOAL_BUDGET_AMOUNTS_QUERY,
        {
            "goalId": goal_id,
            "startMonth": start_month,
            "endMonth": end_month,
        },
    )
    goal = data.get("savingsGoal")
    if not isinstance(goal, dict):
        return []
    return [
        GoalBudgetAmount.from_api(amount)
        for amount in goal.get("monthlyBudgetAmounts") or []
        if isinstance(amount, dict)
    ]


def set_goal_budget_amount(
    session: AuthSession,
    goal_id: str,
    month: str,
    amount: float,
    *,
    apply_to_future: bool = False,
    account_id: str | None = None,
) -> bool:
    data = graphql_request(
        session,
        "Common_SetSavingsGoalBudgetAmount",
        SET_GOAL_BUDGET_AMOUNT_MUTATION,
        {
            "input": {
                "savingsGoalId": goal_id,
                "month": month,
                "amount": amount,
                "applyToFuture": apply_to_future,
                "accountId": account_id,
            }
        },
    )
    payload = _payload(data, "setSavingsGoalBudgetAmount")
    return bool(payload.get("success"))


def _set_goal_account_contribution(
    session: AuthSession,
    goal_id: str,
    account_id: str,
    *,
    contribution_amount: float | None,
    use_entire_balance: bool,
) -> Goal:
    data = graphql_request(
        session,
        "Common_CreateSavingsGoalAccountInitialContributions",
        LINK_GOAL_ACCOUNT_MUTATION,
        {
            "input": {
                "accountId": account_id,
                "contributedGoals": [
                    {
                        "goalId": goal_id,
                        "contributionAmount": contribution_amount,
                        "overrideInitialContribution": True,
                        "useEntireBalance": use_entire_balance,
                    }
                ],
            }
        },
    )
    _payload(data, "createGoalAccountInitialContributions")
    goal = get_goal(session, goal_id)
    if goal is None:
        raise MonarchError("Goal not found after updating account link.")
    return goal


def _create_goal_event(
    session: AuthSession,
    goal_id: str,
    account_id: str,
    *,
    amount: float,
    date: str | None,
    include_in_budget: bool | None,
    notes: str | None,
    operation_name: str,
    mutation: str,
    payload_key: str,
) -> GoalEvent:
    data = graphql_request(
        session,
        operation_name,
        mutation,
        {
            "input": _clean(
                {
                    "id": goal_id,
                    "accountId": account_id,
                    "amount": amount,
                    "date": date,
                    "includeInBudget": include_in_budget,
                    "notes": notes,
                }
            )
        },
    )
    payload = _payload(data, payload_key)
    raw_event = payload.get("goalEvent")
    if not isinstance(raw_event, dict) or raw_event.get("id") is None:
        raise MonarchError("Monarch did not return the created goal event.")
    events = list_goal_events(session, goal_id)
    for event in events:
        if event.id == str(raw_event["id"]):
            return event
    raise MonarchError("Goal event was created but could not be refetched.")


def _payload(data: JsonDict, key: str) -> JsonDict:
    payload = data.get(key)
    if not isinstance(payload, dict):
        raise MonarchError(f"Monarch response did not include {key}.")
    _raise_payload_errors(payload)
    return payload


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
        raise MonarchError("; ".join(messages) or "Monarch returned an error.")
    if isinstance(errors, dict):
        raise MonarchError(str(errors.get("message") or errors))
    raise MonarchError(str(errors))


def _goal_payload(payload: JsonDict, action: str) -> Goal:
    goal = payload.get("savingsGoal")
    if not isinstance(goal, dict):
        raise MonarchError(f"Monarch did not return the {action} goal.")
    return Goal.from_api(goal)


def _goal_event_payload(payload: JsonDict, action: str) -> GoalEvent:
    event = payload.get("goalEvent")
    if not isinstance(event, dict):
        raise MonarchError(f"Monarch did not return the {action} goal event.")
    return GoalEvent.from_api(event)


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _goal_type_value(goal_type: GoalType | str) -> str:
    if isinstance(goal_type, GoalType):
        return goal_type.value
    if isinstance(goal_type, Enum):
        return str(goal_type.value)
    return str(goal_type)


def _status_value(status: GoalStatus | str) -> str:
    if isinstance(status, GoalStatus):
        return status.value
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)
