from __future__ import annotations

from dataclasses import dataclass, field

from monarch_api.types.common import JsonDict
from monarch_api.types.transactions import AccountReference


@dataclass(slots=True)
class InvestmentAccount:
    id: str
    display_name: str
    is_taxable: bool | None = None
    order: int | None = None
    icon: str | None = None
    logo_url: str | None = None
    include_in_net_worth: bool | None = None
    sync_disabled: bool | None = None
    subtype_display: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> InvestmentAccount:
        subtype = _dict(data.get("subtype"))
        return cls(
            id=str(data["id"]),
            display_name=str(data.get("displayName") or ""),
            is_taxable=data.get("isTaxable"),
            order=_int(data.get("order")),
            icon=data.get("icon"),
            logo_url=data.get("logoUrl"),
            include_in_net_worth=data.get("includeInNetWorth"),
            sync_disabled=data.get("syncDisabled"),
            subtype_display=subtype.get("display"),
            raw=dict(data),
        )


@dataclass(slots=True)
class Security:
    id: str
    name: str
    ticker: str | None = None
    type: str | None = None
    type_display: str | None = None
    logo: str | None = None
    current_price: float | None = None
    current_price_updated_at: str | None = None
    closing_price: float | None = None
    closing_price_updated_at: str | None = None
    one_day_change_dollars: float | None = None
    one_day_change_percent: float | None = None
    category_group: str | None = None
    morningstar_category: str | None = None
    global_category: str | None = None
    broad_asset_class: str | None = None
    legal_structure: str | None = None
    prospectus_objective: str | None = None
    aggregated_category: str | None = None
    index_strategy: str | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict | None) -> Security | None:
        if not data:
            return None
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            ticker=data.get("ticker"),
            type=data.get("type"),
            type_display=data.get("typeDisplay"),
            logo=data.get("logo"),
            current_price=_float(data.get("currentPrice")),
            current_price_updated_at=data.get("currentPriceUpdatedAt"),
            closing_price=_float(data.get("closingPrice")),
            closing_price_updated_at=data.get("closingPriceUpdatedAt"),
            one_day_change_dollars=_float(data.get("oneDayChangeDollars")),
            one_day_change_percent=_float(data.get("oneDayChangePercent")),
            category_group=data.get("categoryGroup"),
            morningstar_category=data.get("morningstarCategory"),
            global_category=data.get("globalCategory"),
            broad_asset_class=data.get("broadAssetClass"),
            legal_structure=data.get("legalStructure"),
            prospectus_objective=data.get("prospectusObjective"),
            aggregated_category=data.get("aggregatedCategory"),
            index_strategy=data.get("indexStrategy"),
            raw=dict(data),
        )


@dataclass(slots=True)
class HoldingTaxLot:
    id: str
    created_at: str | None = None
    acquisition_date: str | None = None
    acquisition_quantity: float | None = None
    cost_basis_per_unit: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> HoldingTaxLot:
        return cls(
            id=str(data["id"]),
            created_at=data.get("createdAt"),
            acquisition_date=data.get("acquisitionDate"),
            acquisition_quantity=_float(data.get("acquisitionQuantity")),
            cost_basis_per_unit=_float(data.get("costBasisPerUnit")),
            raw=dict(data),
        )


@dataclass(slots=True)
class Holding:
    id: str
    name: str
    ticker: str | None = None
    type: str | None = None
    type_display: str | None = None
    account: AccountReference | None = None
    security: Security | None = None
    aggregate_id: str | None = None
    quantity: float | None = None
    value: float | None = None
    cost_basis: float | None = None
    user_cost_basis: float | None = None
    closing_price: float | None = None
    closing_price_updated_at: str | None = None
    is_manual: bool | None = None
    aggregate_quantity: float | None = None
    aggregate_cost_basis: float | None = None
    aggregate_total_value: float | None = None
    security_price_change_dollars: float | None = None
    security_price_change_percent: float | None = None
    last_synced_at: str | None = None
    tax_lots: list[HoldingTaxLot] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict,
        *,
        aggregate: JsonDict | None = None,
        security: JsonDict | None = None,
    ) -> Holding:
        aggregate = aggregate or {}
        raw_security = security or data.get("security")
        account = AccountReference.from_api(_dict(data.get("account")))
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or ""),
            ticker=data.get("ticker"),
            type=data.get("type"),
            type_display=data.get("typeDisplay"),
            account=account,
            security=Security.from_api(_dict(raw_security)),
            aggregate_id=(
                str(aggregate["id"])
                if aggregate.get("id") is not None
                else None
            ),
            quantity=_float(data.get("quantity")),
            value=_float(data.get("value")),
            cost_basis=_float(data.get("costBasis")),
            user_cost_basis=_float(data.get("userCostBasis")),
            closing_price=_float(data.get("closingPrice")),
            closing_price_updated_at=data.get("closingPriceUpdatedAt"),
            is_manual=data.get("isManual"),
            aggregate_quantity=_float(aggregate.get("quantity")),
            aggregate_cost_basis=_float(aggregate.get("costBasis")),
            aggregate_total_value=_float(aggregate.get("totalValue")),
            security_price_change_dollars=_float(
                aggregate.get("securityPriceChangeDollars")
            ),
            security_price_change_percent=_float(
                aggregate.get("securityPriceChangePercent")
            ),
            last_synced_at=aggregate.get("lastSyncedAt"),
            tax_lots=[
                HoldingTaxLot.from_api(lot)
                for lot in data.get("taxLots") or []
                if isinstance(lot, dict)
            ],
            raw=dict(data),
        )


@dataclass(slots=True)
class InvestmentPerformancePoint:
    date: str
    value: float | None = None
    return_percent: float | None = None
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> InvestmentPerformancePoint:
        return cls(
            date=str(data["date"]),
            value=_float(data.get("value")),
            return_percent=_float(data.get("returnPercent")),
            raw=dict(data),
        )


@dataclass(slots=True)
class BenchmarkSeries:
    security: Security | None = None
    points: list[InvestmentPerformancePoint] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> BenchmarkSeries:
        return cls(
            security=Security.from_api(_dict(data.get("security"))),
            points=[
                InvestmentPerformancePoint.from_api(point)
                for point in data.get("historicalChart") or []
                if isinstance(point, dict)
            ],
            raw=dict(data),
        )


@dataclass(slots=True)
class PortfolioSummary:
    total_value: float | None = None
    total_change_dollars: float | None = None
    total_change_percent: float | None = None
    one_day_change_dollars: float | None = None
    one_day_change_percent: float | None = None
    holdings_count: int | None = None
    top_movers: list[Security] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(
        cls,
        data: JsonDict | None,
        *,
        holdings_count: int | None = None,
    ) -> PortfolioSummary:
        data = data or {}
        return cls(
            total_value=_float(data.get("totalValue")),
            total_change_dollars=_float(data.get("totalChangeDollars")),
            total_change_percent=_float(data.get("totalChangePercent")),
            one_day_change_dollars=_float(data.get("oneDayChangeDollars")),
            one_day_change_percent=_float(data.get("oneDayChangePercent")),
            holdings_count=holdings_count,
            top_movers=[
                mover
                for mover in (
                    Security.from_api(item)
                    for item in data.get("topMovers") or []
                    if isinstance(item, dict)
                )
                if mover is not None
            ],
            raw=dict(data),
        )


@dataclass(slots=True)
class PortfolioAllocation:
    key: str
    label: str
    value: float
    percent_of_portfolio: float


@dataclass(slots=True)
class Portfolio:
    summary: PortfolioSummary
    holdings: list[Holding] = field(default_factory=list)
    allocations: list[PortfolioAllocation] = field(default_factory=list)
    performance: list[InvestmentPerformancePoint] = field(default_factory=list)
    benchmarks: list[BenchmarkSeries] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> Portfolio:
        holdings = _holdings_from_portfolio(data)
        performance = _dict(data.get("performance"))
        return cls(
            summary=PortfolioSummary.from_api(
                performance,
                holdings_count=len(holdings),
            ),
            holdings=holdings,
            allocations=_allocations(holdings),
            performance=[
                InvestmentPerformancePoint.from_api(point)
                for point in performance.get("historicalChart") or []
                if isinstance(point, dict)
            ],
            benchmarks=[
                BenchmarkSeries.from_api(benchmark)
                for benchmark in performance.get("benchmarks") or []
                if isinstance(benchmark, dict)
            ],
            raw=dict(data),
        )


@dataclass(slots=True)
class InvestmentPerformance:
    security: Security | None = None
    points: list[InvestmentPerformancePoint] = field(default_factory=list)
    raw: JsonDict | None = None

    @classmethod
    def from_api(cls, data: JsonDict) -> InvestmentPerformance:
        return cls(
            security=Security.from_api(_dict(data.get("security"))),
            points=[
                InvestmentPerformancePoint.from_api(point)
                for point in data.get("historicalChart") or []
                if isinstance(point, dict)
            ],
            raw=dict(data),
        )


def _holdings_from_portfolio(data: JsonDict) -> list[Holding]:
    aggregate_holdings = _dict(data.get("aggregateHoldings"))
    edges = aggregate_holdings.get("edges")
    if not isinstance(edges, list):
        return []

    holdings: list[Holding] = []
    for edge in edges:
        node = _dict(_dict(edge).get("node"))
        security = _dict(node.get("security"))
        for holding in node.get("holdings") or []:
            if isinstance(holding, dict):
                holdings.append(
                    Holding.from_api(
                        holding,
                        aggregate=node,
                        security=security,
                    )
                )
    return holdings


def _allocations(holdings: list[Holding]) -> list[PortfolioAllocation]:
    totals: dict[str, float] = {}
    labels: dict[str, str] = {}
    for holding in holdings:
        value = holding.value if holding.value is not None else 0.0
        security = holding.security
        key = (
            security.broad_asset_class
            if security and security.broad_asset_class
            else security.category_group
            if security and security.category_group
            else security.type
            if security and security.type
            else holding.type
            if holding.type
            else "unknown"
        )
        label = (
            security.broad_asset_class
            if security and security.broad_asset_class
            else security.category_group
            if security and security.category_group
            else security.type_display
            if security and security.type_display
            else holding.type_display
            if holding.type_display
            else key
        )
        totals[key] = totals.get(key, 0.0) + value
        labels[key] = label

    total_value = sum(totals.values())
    if total_value == 0:
        return []
    return [
        PortfolioAllocation(
            key=key,
            label=labels[key],
            value=value,
            percent_of_portfolio=value / total_value * 100,
        )
        for key, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


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
