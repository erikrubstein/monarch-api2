from __future__ import annotations

from dataclasses import dataclass

from monarch_api.types.common import JsonDict, User


def _clean(data: JsonDict) -> JsonDict:
    return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class AccountType:
    name: str | None = None
    display_name: str | None = None
    group: str | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> AccountType | None:
        if not data:
            return None
        return cls(
            name=data.get("name"),
            display_name=data.get("display"),
            group=data.get("group"),
        )


@dataclass(slots=True)
class Institution:
    id: str | None = None
    name: str | None = None
    logo: str | None = None
    primary_color: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> Institution | None:
        if not data:
            return None
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            logo=data.get("logo"),
            primary_color=data.get("primaryColor"),
            raw=dict(data),
        )


@dataclass(slots=True)
class Account:
    id: str
    display_name: str
    balance: float | None = None
    current_balance: float | None = None
    last_updated_at: str | None = None
    type: AccountType | None = None
    subtype: AccountType | None = None
    institution: Institution | None = None
    owner: User | None = None
    is_asset: bool | None = None
    is_manual: bool | None = None
    is_hidden: bool | None = None
    sync_disabled: bool | None = None
    include_in_net_worth: bool | None = None
    logo_url: str | None = None
    icon: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Account:
        return cls(
            id=str(data["id"]),
            display_name=str(data.get("displayName") or ""),
            balance=data.get("displayBalance"),
            current_balance=data.get("currentBalance"),
            last_updated_at=data.get("displayLastUpdatedAt"),
            type=AccountType.from_api(data.get("type")),
            subtype=AccountType.from_api(data.get("subtype")),
            institution=Institution.from_api(data.get("institution")),
            owner=User.from_api(data.get("ownedByUser")),
            is_asset=data.get("isAsset"),
            is_manual=data.get("isManual"),
            is_hidden=data.get("isHidden"),
            sync_disabled=data.get("syncDisabled"),
            include_in_net_worth=data.get("includeInNetWorth"),
            logo_url=data.get("logoUrl"),
            icon=data.get("icon"),
            raw=dict(data),
        )


@dataclass(slots=True)
class AccountFilter:
    account_ids: list[str] | None = None
    account_types: list[str] | None = None
    account_subtypes: list[str] | None = None
    groups: list[str] | None = None
    include_hidden: bool | None = None
    include_deleted: bool | None = None

    def to_api(self) -> JsonDict:
        return _clean(
            {
                "ids": self.account_ids,
                "accountTypes": self.account_types,
                "accountSubtypes": self.account_subtypes,
                "groups": self.groups,
                "includeHidden": self.include_hidden,
                "includeDeleted": self.include_deleted,
            }
        )


@dataclass(slots=True)
class AccountBalance:
    account_id: str
    balance: float | None = None
    include_in_net_worth: bool | None = None
    account_type: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> AccountBalance:
        account_type = data.get("type")
        return cls(
            account_id=str(data["id"]),
            balance=data.get("displayBalance"),
            include_in_net_worth=data.get("includeInNetWorth"),
            account_type=account_type.get("name") if isinstance(account_type, dict) else None,
            raw=dict(data),
        )


@dataclass(slots=True)
class AccountHistoryPoint:
    account_id: str
    date: str
    balance: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict, *, account_id: str) -> AccountHistoryPoint:
        return cls(
            account_id=account_id,
            date=str(data["date"]),
            balance=data.get("signedBalance"),
            raw=dict(data),
        )


@dataclass(slots=True)
class NetWorthBreakdownPoint:
    account_type: str
    date: str
    balance: float | None = None
    account_group: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        account_group: str | None = None,
    ) -> NetWorthBreakdownPoint:
        return cls(
            account_type=str(data["accountType"]),
            date=str(data["month"]),
            balance=data.get("balance"),
            account_group=account_group,
            raw=dict(data),
        )


@dataclass(slots=True)
class NetWorthSnapshot:
    date: str
    net_worth: float | None = None
    assets_balance: float | None = None
    liabilities_balance: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> NetWorthSnapshot:
        return cls(
            date=str(data["date"]),
            net_worth=data.get("balance"),
            assets_balance=data.get("assetsBalance"),
            liabilities_balance=data.get("liabilitiesBalance"),
            raw=dict(data),
        )
