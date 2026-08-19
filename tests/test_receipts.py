from __future__ import annotations

from monarch_api import Receipt, ReceiptFilter, ReceiptSource, ReceiptStatus
from monarch_api.functions import receipts


def test_receipt_maps_backend_vendor_to_source() -> None:
    receipt = Receipt.from_api(
        {
            "id": "receipt-1",
            "vendor": "email_import",
            "status": "pending_matches",
        }
    )

    assert receipt.source == ReceiptSource.EMAIL


def test_receipt_filter_maps_public_source_to_backend_vendor() -> None:
    filters = ReceiptFilter(
        status=ReceiptStatus.PENDING_MATCHES,
        source=ReceiptSource.UPLOAD,
    )

    assert filters.to_api() == {
        "status": "pending_matches",
        "vendor": "user_import",
    }


def test_list_receipts_merges_uploads_and_email_before_pagination(
    monkeypatch,
) -> None:
    records = {
        "user_import": [
            _receipt("upload-3", "user_import", "2026-08-03T00:00:00Z"),
            _receipt("upload-1", "user_import", "2026-08-01T00:00:00Z"),
        ],
        "email_import": [
            _receipt("email-4", "email_import", "2026-08-04T00:00:00Z"),
            _receipt("email-2", "email_import", "2026-08-02T00:00:00Z"),
        ],
    }

    def fake_graphql_request(session, operation_name, query, variables):
        source_records = records[variables["filters"]["vendor"]]
        offset = variables["offset"]
        limit = variables["limit"]
        return {
            "retailSyncsWithTotal": {
                "totalCount": len(source_records),
                "results": source_records[offset : offset + limit],
            }
        }

    monkeypatch.setattr(receipts, "graphql_request", fake_graphql_request)

    page = receipts.list_receipts(object(), limit=2, offset=1)

    assert page.total_count == 4
    assert [receipt.id for receipt in page.receipts] == ["upload-3", "email-2"]


def test_list_receipts_with_source_uses_backend_pagination(monkeypatch) -> None:
    captured = {}

    def fake_graphql_request(session, operation_name, query, variables):
        captured.update(variables)
        return {"retailSyncsWithTotal": {"totalCount": 12, "results": []}}

    monkeypatch.setattr(receipts, "graphql_request", fake_graphql_request)

    page = receipts.list_receipts(
        object(),
        filters=ReceiptFilter(source=ReceiptSource.EMAIL),
        limit=25,
        offset=5,
    )

    assert page.total_count == 12
    assert captured["filters"] == {"vendor": "email_import"}
    assert captured["limit"] == 25
    assert captured["offset"] == 5


def _receipt(receipt_id: str, vendor: str, created_at: str) -> dict[str, object]:
    return {
        "id": receipt_id,
        "vendor": vendor,
        "status": "pending_matches",
        "createdAt": created_at,
        "orders": [],
        "attachments": [],
    }
