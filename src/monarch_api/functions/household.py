from __future__ import annotations

from monarch_api.functions.common import MonarchError, graphql_request
from monarch_api.types.auth import AuthSession
from monarch_api.types.common import JsonDict
from monarch_api.types.household import (
    Household,
    HouseholdMember,
    HouseholdPreferences,
    UserProfile,
)


HOUSEHOLD_FIELDS = """
fragment HouseholdFields on Household {
  id
  name
  address
  city
  state
  zipCode
  country
}
"""

HOUSEHOLD_MEMBER_FIELDS = """
fragment HouseholdMemberFields on User {
  id
  name
  displayName
  email
  householdRole
  hasMfaOn
  profilePictureUrl
}
"""

USER_PROFILE_FIELDS = """
fragment UserProfileFields on User {
  id
  email
  name
  displayName
  timezone
  householdRole
  hasPassword
  hasMfaOn
  isSuperuser
  profilePictureUrl
  createdAt
  pendingEmailUpdateVerification {
    email
  }
}
"""

HOUSEHOLD_PREFERENCES_FIELDS = """
fragment HouseholdPreferencesFields on HouseholdPreferences {
  id
  newTransactionsNeedReview
  uncategorizedTransactionsNeedReview
  pendingTransactionsCanBeEdited
  accountGroupOrder
  aiAssistantEnabled
  llmEnrichmentEnabled
  investmentTransactionsEnabled
  budgetApplyToFutureMonthsDefault
  hiddenTransactionsBetaEnabled
  collaborationToolsEnabled
  aggDataSharingEnabled
  aiModelTrainingOnUserDataEnabled
  excludeBusinessFromBudget
  continuousFinancialMonitoringEnabled
  eligibleForFinancialInsights
}
"""

GET_HOUSEHOLD_QUERY = (
    """
query Common_GetMyHousehold {
  myHousehold {
    ...HouseholdFields
  }
}
"""
    + HOUSEHOLD_FIELDS
)

LIST_HOUSEHOLD_MEMBERS_QUERY = (
    """
query Common_GetHouseholdMembers {
  myHousehold {
    id
    users {
      ...HouseholdMemberFields
    }
  }
}
"""
    + HOUSEHOLD_MEMBER_FIELDS
)

GET_CURRENT_USER_QUERY = (
    """
query Common_GetMe {
  me {
    ...UserProfileFields
  }
}
"""
    + USER_PROFILE_FIELDS
)

GET_HOUSEHOLD_PREFERENCES_QUERY = (
    """
query Common_GetHouseholdPreferences {
  householdPreferences {
    ...HouseholdPreferencesFields
  }
  budgetSystem
  budgetApplyToFutureMonthsDefault
}
"""
    + HOUSEHOLD_PREFERENCES_FIELDS
)

UPDATE_CURRENT_USER_MUTATION = (
    """
mutation Common_UpdateMe($input: UpdateMeInput!) {
  updateMe(input: $input) {
    user {
      ...UserProfileFields
    }
    errors {
      message
      code
    }
  }
}
"""
    + USER_PROFILE_FIELDS
)

UPDATE_HOUSEHOLD_PREFERENCES_MUTATION = (
    """
mutation Common_UpdateHouseholdPreferences($input: UpdateHouseholdPreferencesInput!) {
  updateHouseholdPreferences(input: $input) {
    householdPreferences {
      ...HouseholdPreferencesFields
    }
  }
}
"""
    + HOUSEHOLD_PREFERENCES_FIELDS
)


def get_household(session: AuthSession) -> Household:
    data = graphql_request(session, "Common_GetMyHousehold", GET_HOUSEHOLD_QUERY)
    household = data.get("myHousehold")
    if not isinstance(household, dict):
        raise MonarchError("Monarch did not return the current household.")
    return Household.from_api(household)


def list_household_members(session: AuthSession) -> list[HouseholdMember]:
    data = graphql_request(
        session,
        "Common_GetHouseholdMembers",
        LIST_HOUSEHOLD_MEMBERS_QUERY,
    )
    household = data.get("myHousehold")
    if not isinstance(household, dict):
        return []
    users = household.get("users")
    if not isinstance(users, list):
        return []
    return [HouseholdMember.from_api(user) for user in users if isinstance(user, dict)]


def get_household_member(
    session: AuthSession,
    member_id: str,
) -> HouseholdMember | None:
    for member in list_household_members(session):
        if member.id == member_id:
            return member
    return None


def get_current_user(session: AuthSession) -> UserProfile:
    data = graphql_request(session, "Common_GetMe", GET_CURRENT_USER_QUERY)
    user = data.get("me")
    if not isinstance(user, dict):
        raise MonarchError("Monarch did not return the current user.")
    return UserProfile.from_api(user)


def update_current_user(
    session: AuthSession,
    *,
    display_name: str | None = None,
    timezone: str | None = None,
) -> UserProfile:
    input_data = _clean(
        {
            "displayName": display_name,
            "timezone": timezone,
        }
    )
    if not input_data:
        return get_current_user(session)

    data = graphql_request(
        session,
        "Common_UpdateMe",
        UPDATE_CURRENT_USER_MUTATION,
        {"input": input_data},
    )
    payload = _payload(data, "updateMe")
    _raise_payload_errors(payload)
    user = payload.get("user")
    if not isinstance(user, dict):
        raise MonarchError("Monarch did not return the updated current user.")
    return UserProfile.from_api(user)


def get_household_preferences(session: AuthSession) -> HouseholdPreferences:
    data = graphql_request(
        session,
        "Common_GetHouseholdPreferences",
        GET_HOUSEHOLD_PREFERENCES_QUERY,
    )
    return _household_preferences(data)


def update_household_preferences(
    session: AuthSession,
    *,
    new_transactions_need_review: bool | None = None,
    uncategorized_transactions_need_review: bool | None = None,
    pending_transactions_can_be_edited: bool | None = None,
    hidden_transactions_beta_enabled: bool | None = None,
    exclude_business_from_budget: bool | None = None,
) -> HouseholdPreferences:
    input_data = _clean(
        {
            "newTransactionsNeedReview": new_transactions_need_review,
            "uncategorizedTransactionsNeedReview": (
                uncategorized_transactions_need_review
            ),
            "pendingTransactionsCanBeEdited": pending_transactions_can_be_edited,
            "hiddenTransactionsBetaEnabled": hidden_transactions_beta_enabled,
            "excludeBusinessFromBudget": exclude_business_from_budget,
        }
    )
    if not input_data:
        return get_household_preferences(session)

    data = graphql_request(
        session,
        "Common_UpdateHouseholdPreferences",
        UPDATE_HOUSEHOLD_PREFERENCES_MUTATION,
        {"input": input_data},
    )
    payload = _payload(data, "updateHouseholdPreferences")
    preferences = payload.get("householdPreferences")
    if not isinstance(preferences, dict):
        raise MonarchError("Monarch did not return updated household preferences.")
    return get_household_preferences(session)


def _household_preferences(data: JsonDict) -> HouseholdPreferences:
    preferences = data.get("householdPreferences")
    if not isinstance(preferences, dict):
        raise MonarchError("Monarch did not return household preferences.")
    budget_system = data.get("budgetSystem")
    return HouseholdPreferences.from_api(
        preferences,
        budget_system=str(budget_system) if budget_system is not None else None,
        budget_apply_to_future_months_default=data.get(
            "budgetApplyToFutureMonthsDefault"
        ),
    )


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


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}
