from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from monarch_api.types.common import JsonDict


class HouseholdRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"
    ADVISOR = "advisor"


@dataclass(slots=True)
class Household:
    id: str
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Household:
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zipCode"),
            country=data.get("country"),
            raw=dict(data),
        )


@dataclass(slots=True)
class HouseholdMember:
    id: str
    name: str | None = None
    display_name: str | None = None
    email: str | None = None
    role: HouseholdRole | None = None
    has_mfa_on: bool | None = None
    profile_picture_url: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> HouseholdMember:
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            display_name=data.get("displayName"),
            email=data.get("email"),
            role=_role(data.get("householdRole")),
            has_mfa_on=data.get("hasMfaOn"),
            profile_picture_url=data.get("profilePictureUrl"),
            raw=dict(data),
        )


@dataclass(slots=True)
class UserProfile:
    id: str
    email: str | None = None
    name: str | None = None
    display_name: str | None = None
    timezone: str | None = None
    household_role: HouseholdRole | None = None
    has_password: bool | None = None
    has_mfa_on: bool | None = None
    is_superuser: bool | None = None
    profile_picture_url: str | None = None
    created_at: str | None = None
    pending_email_update: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> UserProfile:
        pending_email_update = _dict(data.get("pendingEmailUpdateVerification"))
        return cls(
            id=str(data["id"]),
            email=data.get("email"),
            name=data.get("name"),
            display_name=data.get("displayName"),
            timezone=data.get("timezone"),
            household_role=_role(data.get("householdRole")),
            has_password=data.get("hasPassword"),
            has_mfa_on=data.get("hasMfaOn"),
            is_superuser=data.get("isSuperuser"),
            profile_picture_url=data.get("profilePictureUrl"),
            created_at=data.get("createdAt"),
            pending_email_update=pending_email_update.get("email"),
            raw=dict(data),
        )


@dataclass(slots=True)
class HouseholdPreferences:
    id: str
    new_transactions_need_review: bool | None = None
    uncategorized_transactions_need_review: bool | None = None
    pending_transactions_can_be_edited: bool | None = None
    account_group_order: list[str] | None = None
    ai_assistant_enabled: bool | None = None
    llm_enrichment_enabled: bool | None = None
    investment_transactions_enabled: bool | None = None
    budget_apply_to_future_months_default: bool | None = None
    hidden_transactions_beta_enabled: bool | None = None
    collaboration_tools_enabled: bool | None = None
    agg_data_sharing_enabled: bool | None = None
    ai_model_training_on_user_data_enabled: bool | None = None
    exclude_business_from_budget: bool | None = None
    continuous_financial_monitoring_enabled: bool | None = None
    eligible_for_financial_insights: bool | None = None
    budget_system: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        budget_system: str | None = None,
        budget_apply_to_future_months_default: bool | None = None,
    ) -> HouseholdPreferences:
        return cls(
            id=str(data["id"]),
            new_transactions_need_review=data.get("newTransactionsNeedReview"),
            uncategorized_transactions_need_review=data.get(
                "uncategorizedTransactionsNeedReview"
            ),
            pending_transactions_can_be_edited=data.get(
                "pendingTransactionsCanBeEdited"
            ),
            account_group_order=_str_list(data.get("accountGroupOrder")),
            ai_assistant_enabled=data.get("aiAssistantEnabled"),
            llm_enrichment_enabled=data.get("llmEnrichmentEnabled"),
            investment_transactions_enabled=data.get("investmentTransactionsEnabled"),
            budget_apply_to_future_months_default=(
                data.get("budgetApplyToFutureMonthsDefault")
                if data.get("budgetApplyToFutureMonthsDefault") is not None
                else budget_apply_to_future_months_default
            ),
            hidden_transactions_beta_enabled=data.get("hiddenTransactionsBetaEnabled"),
            collaboration_tools_enabled=data.get("collaborationToolsEnabled"),
            agg_data_sharing_enabled=data.get("aggDataSharingEnabled"),
            ai_model_training_on_user_data_enabled=data.get(
                "aiModelTrainingOnUserDataEnabled"
            ),
            exclude_business_from_budget=data.get("excludeBusinessFromBudget"),
            continuous_financial_monitoring_enabled=data.get(
                "continuousFinancialMonitoringEnabled"
            ),
            eligible_for_financial_insights=data.get("eligibleForFinancialInsights"),
            budget_system=budget_system,
            raw=dict(data),
        )


def _role(value: object) -> HouseholdRole | None:
    if value is None:
        return None
    return HouseholdRole(str(value).lower())


def _dict(value: object) -> JsonDict:
    if isinstance(value, dict):
        return value
    return {}


def _str_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [str(item) for item in value]
