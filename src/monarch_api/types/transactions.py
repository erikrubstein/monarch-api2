from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monarch_api.types.categories import CategoryType, _category_type
from monarch_api.types.common import JsonDict, User


class TransactionReviewStatus(str, Enum):
    REVIEWED = "reviewed"
    NEEDS_REVIEW = "needs_review"


class TransactionSort(str, Enum):
    DATE_DESCENDING = "date"
    DATE_ASCENDING = "inverse_date"
    AMOUNT_DESCENDING = "amount"
    AMOUNT_ASCENDING = "inverse_amount"


class TransactionVisibility(str, Enum):
    ALL = "all_transactions"
    VISIBLE_ONLY = "non_hidden_transactions_only"
    HIDDEN_ONLY = "hidden_transactions_only"


@dataclass(slots=True)
class AccountReference:
    id: str
    display_name: str
    icon: str | None = None
    logo_url: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> AccountReference | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            display_name=str(data.get("displayName") or ""),
            icon=data.get("icon"),
            logo_url=data.get("logoUrl"),
            raw=dict(data),
        )


@dataclass(slots=True)
class MerchantReference:
    id: str
    name: str
    logo_url: str | None = None
    transaction_count: int | None = None
    recurring_id: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> MerchantReference | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            logo_url=data.get("logoUrl"),
            transaction_count=_first_present(data, "transactionCount", "transactionsCount"),
            recurring_id=_nested_id(data.get("recurringTransactionStream")),
            raw=dict(data),
        )


@dataclass(slots=True)
class CategoryReference:
    id: str
    name: str
    icon: str | None = None
    group_id: str | None = None
    type: CategoryType | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> CategoryReference | None:
        if not data:
            return None
        group = data.get("group")
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            icon=data.get("icon"),
            group_id=_nested_id(group),
            type=_category_type(group.get("type")) if isinstance(group, dict) else None,
            raw=dict(data),
        )


@dataclass(slots=True)
class TagReference:
    id: str
    name: str
    color: str | None = None
    order: int | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> TagReference | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            color=data.get("color"),
            order=data.get("order"),
            raw=dict(data),
        )


@dataclass(slots=True)
class GoalReference:
    id: str
    name: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> GoalReference | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=data.get("name"),
            raw=dict(data),
        )


@dataclass(slots=True)
class TransactionAttachment:
    id: str
    public_id: str | None = None
    extension: str | None = None
    size_bytes: int | None = None
    filename: str | None = None
    original_asset_url: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> TransactionAttachment | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            public_id=data.get("publicId"),
            extension=data.get("extension"),
            size_bytes=_int_or_none(data.get("sizeBytes")),
            filename=data.get("filename"),
            original_asset_url=data.get("originalAssetUrl"),
            raw=dict(data),
        )


@dataclass(slots=True)
class Transaction:
    id: str
    date: str
    amount: float
    pending: bool | None = None
    account: AccountReference | None = None
    merchant: MerchantReference | None = None
    merchant_name: str = ""
    original_statement: str | None = None
    category: CategoryReference | None = None
    tags: list[TagReference] = field(default_factory=list)
    notes: str | None = None
    review_status: TransactionReviewStatus | None = None
    needs_review: bool | None = None
    needs_review_by_user: User | None = None
    reviewed_at: str | None = None
    reviewed_by_user: User | None = None
    hide_from_reports: bool | None = None
    hidden_by_account: bool | None = None
    is_split: bool | None = None
    has_splits: bool | None = None
    is_recurring: bool | None = None
    recurring_id: str | None = None
    goal: GoalReference | None = None
    original_transaction_id: str | None = None
    attachments: list[TransactionAttachment] = field(default_factory=list)
    attachment_count: int = 0
    owner: User | None = None
    is_manual: bool | None = None
    synced_from_institution: bool | None = None
    imported_from_mint: bool | None = None
    deleted_at: str | None = None
    updated_at: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Transaction:
        merchant = MerchantReference.from_api(data.get("merchant"))
        tags = [
            tag
            for tag in (TagReference.from_api(tag) for tag in data.get("tags") or [])
            if tag is not None
        ]
        attachments = [
            attachment
            for attachment in (
                TransactionAttachment.from_api(attachment)
                for attachment in data.get("attachments") or []
            )
            if attachment is not None
        ]
        return cls(
            id=str(data["id"]),
            date=str(data.get("date") or ""),
            amount=float(data.get("amount") or 0),
            pending=data.get("pending"),
            account=AccountReference.from_api(data.get("account")),
            merchant=merchant,
            merchant_name=_merchant_name(data, merchant),
            original_statement=data.get("dataProviderDescription") or data.get("plaidName"),
            category=CategoryReference.from_api(data.get("category")),
            tags=tags,
            notes=data.get("notes"),
            review_status=_review_status(data.get("reviewStatus")),
            needs_review=data.get("needsReview"),
            needs_review_by_user=User.from_api(data.get("needsReviewByUser")),
            reviewed_at=data.get("reviewedAt"),
            reviewed_by_user=User.from_api(data.get("reviewedByUser")),
            hide_from_reports=data.get("hideFromReports"),
            hidden_by_account=data.get("hiddenByAccount"),
            is_split=data.get("isSplitTransaction"),
            has_splits=data.get("hasSplitTransactions"),
            is_recurring=data.get("isRecurring"),
            recurring_id=merchant.recurring_id if merchant is not None else None,
            goal=_goal_reference(data),
            original_transaction_id=_nested_id(data.get("originalTransaction")),
            attachments=attachments,
            attachment_count=len(attachments),
            owner=User.from_api(data.get("ownedByUser")),
            is_manual=data.get("isManual"),
            synced_from_institution=data.get("syncedFromInstitution"),
            imported_from_mint=data.get("importedFromMint"),
            deleted_at=data.get("deletedAt"),
            updated_at=data.get("updatedAt"),
            raw=dict(data),
        )


@dataclass(slots=True)
class TransactionSplit:
    id: str
    amount: float
    date: str | None = None
    merchant: MerchantReference | None = None
    merchant_name: str = ""
    category: CategoryReference | None = None
    goal: GoalReference | None = None
    tags: list[TagReference] = field(default_factory=list)
    notes: str | None = None
    hide_from_reports: bool | None = None
    review_status: TransactionReviewStatus | None = None
    needs_review: bool | None = None
    needs_review_by_user: User | None = None
    owner: User | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> TransactionSplit:
        merchant = MerchantReference.from_api(data.get("merchant"))
        tags = [
            tag
            for tag in (TagReference.from_api(tag) for tag in data.get("tags") or [])
            if tag is not None
        ]
        return cls(
            id=str(data["id"]),
            amount=float(data.get("amount") or 0),
            date=data.get("date"),
            merchant=merchant,
            merchant_name=_merchant_name(data, merchant),
            category=CategoryReference.from_api(data.get("category")),
            goal=_goal_reference(data),
            tags=tags,
            notes=data.get("notes"),
            hide_from_reports=data.get("hideFromReports"),
            review_status=_review_status(data.get("reviewStatus")),
            needs_review=data.get("needsReview"),
            needs_review_by_user=User.from_api(data.get("needsReviewByUser")),
            owner=User.from_api(data.get("ownedByUser")),
            raw=dict(data),
        )


@dataclass(slots=True)
class TransactionSplitDetails:
    transaction: Transaction
    splits: list[TransactionSplit]


@dataclass(slots=True)
class TransactionSplitDraft:
    amount: float
    id: str | None = None
    date: str | None = None
    merchant_name: str | None = None
    category_id: str | None = None
    notes: str | None = None
    hide_from_reports: bool | None = None
    review_status: TransactionReviewStatus | None = None
    needs_review: bool | None = None
    needs_review_by_user_id: str | None = None
    owner_user_id: str | None = None
    tag_ids: list[str] | None = None
    goal_id: str | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "id": self.id,
                "amount": self.amount,
                "date": self.date,
                "merchantName": self.merchant_name,
                "categoryId": self.category_id,
                "notes": self.notes,
                "hideFromReports": self.hide_from_reports,
                "reviewStatus": (
                    self.review_status.value
                    if self.review_status is not None
                    else None
                ),
                "needsReview": self.needs_review,
                "needsReviewByUserId": self.needs_review_by_user_id,
                "ownerUserId": self.owner_user_id,
                "tags": self.tag_ids,
                "goalId": self.goal_id,
            }
        )


@dataclass(slots=True)
class TransactionPage:
    transactions: list[Transaction]
    total_count: int
    limit: int
    offset: int


@dataclass(slots=True)
class TransactionFilter:
    start_date: str | None = None
    end_date: str | None = None
    search: str | None = None
    transaction_ids: list[str] | None = None
    account_ids: list[str] | None = None
    category_ids: list[str] | None = None
    category_group_ids: list[str] | None = None
    merchant_ids: list[str] | None = None
    tag_ids: list[str] | None = None
    goal_ids: list[str] | None = None
    min_absolute_amount: float | None = None
    max_absolute_amount: float | None = None
    category_type: CategoryType | None = None
    credits_only: bool | None = None
    debits_only: bool | None = None
    is_pending: bool | None = None
    is_recurring: bool | None = None
    is_split: bool | None = None
    is_uncategorized: bool | None = None
    is_untagged: bool | None = None
    has_notes: bool | None = None
    has_attachments: bool | None = None
    hide_from_reports: bool | None = None
    needs_review: bool | None = None
    needs_review_by_user_id: str | None = None
    needs_review_unassigned: bool | None = None
    synced_from_institution: bool | None = None
    imported_from_mint: bool | None = None
    transaction_visibility: TransactionVisibility | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "startDate": self.start_date,
                "endDate": self.end_date,
                "search": self.search,
                "ids": self.transaction_ids,
                "accounts": self.account_ids,
                "categories": self.category_ids,
                "categoryGroups": self.category_group_ids,
                "merchants": self.merchant_ids,
                "tags": self.tag_ids,
                "goals": self.goal_ids,
                "absAmountGte": self.min_absolute_amount,
                "absAmountLte": self.max_absolute_amount,
                "categoryType": (
                    self.category_type.value if self.category_type is not None else None
                ),
                "creditsOnly": self.credits_only,
                "debitsOnly": self.debits_only,
                "isPending": self.is_pending,
                "isRecurring": self.is_recurring,
                "isSplit": self.is_split,
                "isUncategorized": self.is_uncategorized,
                "isUntagged": self.is_untagged,
                "hasNotes": self.has_notes,
                "hasAttachments": self.has_attachments,
                "hideFromReports": self.hide_from_reports,
                "needsReview": self.needs_review,
                "needsReviewByUser": self.needs_review_by_user_id,
                "needsReviewUnassigned": self.needs_review_unassigned,
                "syncedFromInstitution": self.synced_from_institution,
                "importedFromMint": self.imported_from_mint,
                "transactionVisibility": (
                    self.transaction_visibility.value
                    if self.transaction_visibility is not None
                    else None
                ),
            }
        )


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _first_present(data: JsonDict, *keys: str) -> int | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, int):
            return value
    return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _goal_reference(data: JsonDict) -> GoalReference | None:
    direct_goal = GoalReference.from_api(data.get("goal"))
    if direct_goal is not None:
        return direct_goal
    savings_goal_event = data.get("savingsGoalEvent")
    if not isinstance(savings_goal_event, dict):
        return None
    return GoalReference.from_api(savings_goal_event.get("goal"))


def _merchant_name(
    data: JsonDict,
    merchant: MerchantReference | None,
) -> str:
    if merchant is not None and merchant.name:
        return merchant.name
    return str(
        data.get("merchantName")
        or data.get("dataProviderDescription")
        or data.get("plaidName")
        or ""
    )


def _nested_id(data: object) -> str | None:
    if not isinstance(data, dict) or data.get("id") is None:
        return None
    return str(data["id"])


def _review_status(value: object) -> TransactionReviewStatus | None:
    if value is None:
        return None
    try:
        return TransactionReviewStatus(str(value))
    except ValueError:
        return None
