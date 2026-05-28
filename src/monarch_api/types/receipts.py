from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import CategoryReference, MerchantReference


class ReceiptStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    PENDING_MATCHES = "pending_matches"


class ReceiptTransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    TIP = "tip"


@dataclass(slots=True)
class ReceiptAttachment:
    id: str
    storage_id: str | None = None
    filename: str | None = None
    extension: str | None = None
    size_bytes: int | None = None
    original_asset_url: str | None = None
    thumbnail_url: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptAttachment | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            storage_id=data.get("storageId"),
            filename=data.get("filename"),
            extension=data.get("extension"),
            size_bytes=_int_or_none(data.get("sizeBytes")),
            original_asset_url=data.get("originalAssetUrl"),
            thumbnail_url=data.get("thumbnailUrl"),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReceiptLineItem:
    id: str
    title: str
    quantity: int | None = None
    price: float | None = None
    total: float | None = None
    is_associated_to_transaction: bool | None = None
    category: CategoryReference | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptLineItem | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            title=str(data.get("title") or ""),
            quantity=_int_or_none(data.get("quantity")),
            price=_float_or_none(data.get("price")),
            total=_float_or_none(data.get("total")),
            is_associated_to_transaction=data.get("isAssociatedToRetailTransaction"),
            category=CategoryReference.from_api(data.get("category")),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReceiptLinkedTransaction:
    id: str
    is_manual: bool | None = None
    has_splits: bool | None = None
    merchant: MerchantReference | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptLinkedTransaction | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            is_manual=data.get("isManual"),
            has_splits=data.get("hasSplitTransactions"),
            merchant=MerchantReference.from_api(data.get("merchant")),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReceiptTransaction:
    id: str
    date: str | None = None
    total: float | None = None
    type: ReceiptTransactionType | None = None
    transaction_update_skipped: bool | None = None
    linked_transaction: ReceiptLinkedTransaction | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptTransaction | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            date=data.get("date"),
            total=_float_or_none(data.get("total")),
            type=_receipt_transaction_type(data.get("transactionType")),
            transaction_update_skipped=data.get("transactionUpdateSkipped"),
            linked_transaction=ReceiptLinkedTransaction.from_api(data.get("transaction")),
            raw=dict(data),
        )


@dataclass(slots=True)
class ReceiptOrder:
    id: str
    merchant_name: str | None = None
    date: str | None = None
    total_for_products: float | None = None
    shipping: float | None = None
    delivery_fee: float | None = None
    additional_charges: float | None = None
    adjustments_amount: float | None = None
    total_before_tax: float | None = None
    tax: float | None = None
    tip: float | None = None
    gift_card_amount: float | None = None
    grand_total: float | None = None
    display_status: str | None = None
    line_items: list[ReceiptLineItem] = field(default_factory=list)
    transaction: ReceiptTransaction | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptOrder | None:
        if not data:
            return None
        line_items = [
            line_item
            for line_item in (
                ReceiptLineItem.from_api(item)
                for item in data.get("retailLineItems") or []
            )
            if line_item is not None
        ]
        transactions = [
            transaction
            for transaction in (
                ReceiptTransaction.from_api(item)
                for item in data.get("retailTransactions") or []
            )
            if transaction is not None
        ]
        return cls(
            id=str(data["id"]),
            merchant_name=data.get("merchantName"),
            date=data.get("date"),
            total_for_products=_float_or_none(data.get("totalForProducts")),
            shipping=_float_or_none(data.get("shipping")),
            delivery_fee=_float_or_none(data.get("deliveryFee")),
            additional_charges=_float_or_none(data.get("additionalCharges")),
            adjustments_amount=_float_or_none(data.get("adjustmentsAmount")),
            total_before_tax=_float_or_none(data.get("totalBeforeTax")),
            tax=_float_or_none(data.get("tax")),
            tip=_float_or_none(data.get("tip")),
            gift_card_amount=_float_or_none(data.get("giftCardAmount")),
            grand_total=_float_or_none(data.get("grandTotal")),
            display_status=data.get("displayStatus"),
            line_items=line_items,
            transaction=transactions[0] if transactions else None,
            raw=dict(data),
        )


@dataclass(slots=True)
class Receipt:
    id: str
    status: ReceiptStatus | None = None
    started_at: str | None = None
    ended_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    order: ReceiptOrder | None = None
    transaction: ReceiptTransaction | None = None
    attachment: ReceiptAttachment | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Receipt:
        orders = [
            order
            for order in (
                ReceiptOrder.from_api(item) for item in data.get("orders") or []
            )
            if order is not None
        ]
        attachments = [
            attachment
            for attachment in (
                ReceiptAttachment.from_api(item)
                for item in data.get("attachments") or []
            )
            if attachment is not None
        ]
        order = orders[0] if orders else None
        return cls(
            id=str(data["id"]),
            status=_receipt_status(data.get("status")),
            started_at=data.get("startedAt"),
            ended_at=data.get("endedAt"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            order=order,
            transaction=order.transaction if order is not None else None,
            attachment=attachments[0] if attachments else None,
            raw=dict(data),
        )

    @property
    def is_matched(self) -> bool:
        return (
            self.transaction is not None
            and self.transaction.linked_transaction is not None
        )

    @property
    def transaction_id(self) -> str | None:
        if self.transaction is None or self.transaction.linked_transaction is None:
            return None
        return self.transaction.linked_transaction.id


@dataclass(slots=True)
class ReceiptPage:
    receipts: list[Receipt]
    total_count: int
    limit: int
    offset: int


@dataclass(slots=True)
class ReceiptFilter:
    status: ReceiptStatus | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "status": self.status.value if self.status is not None else None,
                "vendor": "user_import",
            }
        )


@dataclass(slots=True)
class ReceiptLineItemUpdate:
    line_item_id: str
    title: str | None = None
    category_id: str | None = None
    price: float | None = None
    quantity: int | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "retailLineItemId": self.line_item_id,
                "title": self.title,
                "categoryId": self.category_id,
                "price": self.price,
                "quantity": self.quantity,
            }
        )


@dataclass(slots=True)
class ReceiptSettings:
    auto_categorize: bool | None = None
    update_transaction_notes: bool | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> ReceiptSettings:
        if data is None:
            return cls()
        return cls(
            auto_categorize=data.get("shouldCategorizeAndSplitTransactions"),
            update_transaction_notes=data.get("shouldUpdateTransactionsNotes"),
            raw=dict(data),
        )


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float | str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _receipt_status(value: object) -> ReceiptStatus | None:
    if value is None:
        return None
    try:
        return ReceiptStatus(str(value))
    except ValueError:
        return None


def _receipt_transaction_type(value: object) -> ReceiptTransactionType | None:
    if value is None:
        return None
    try:
        return ReceiptTransactionType(str(value))
    except ValueError:
        return None
