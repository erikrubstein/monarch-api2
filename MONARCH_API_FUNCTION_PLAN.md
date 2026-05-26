# Monarch API Function Plan

This document defines a user-task-oriented API surface for an unofficial Monarch Money client. The goal is not to map every discovered GraphQL operation. The goal is to expose the practical capabilities a person uses in the Monarch web app, grouped by product area, with clear ownership boundaries so functions do not overlap.

## Design Principles

- Prefer page-level workflows over raw endpoint names.
- Keep each domain object owned by one group. Other groups should reference it by id or reuse shared filters.
- Favor composable reads and focused mutations. For example, `Transactions.list_transactions(filter=...)` should support most search and drilldown use cases instead of adding one function per filter.
- Use precise data types for inputs and outputs. Avoid returning untyped dictionaries once the model is understood.
- Treat unstable or provider-driven capabilities, such as account-linking flows and investment data, as best-effort features with explicit limitations.

## Ownership Boundaries

| Concept | Owning group | Referenced by |
| --- | --- | --- |
| Authentication, session tokens, MFA, password reset | Auth | All authenticated groups |
| Accounts and account balances | Accounts | Transactions, Cashflow, Reports, Budget, Recurring, Goals, Investments, Rules |
| Transactions and transaction edits | Transactions | Cashflow, Reports, Budget, Recurring, Goals, Rules |
| Cashflow summary and categorized money movement | Cashflow | Reports, Budget |
| Saved and generic visual reports | Reports | Transactions, Cashflow |
| Budget plans and monthly budget rows | Budget | Categories, Goals |
| Recurring merchant/series detection | Recurring | Transactions, Rules |
| Goals and goal links | Goals | Transactions, Budget, Rules, Accounts |
| Holdings, securities, allocation, performance | Investments | Accounts |
| Categories and category groups | Categories | Transactions, Cashflow, Reports, Budget, Rules |
| Merchant metadata | Merchants | Transactions, Reports, Recurring, Rules |
| Rules and automation order | Rules | Transactions, Categories, Tags, Merchants, Goals |
| Tag definitions | Tags | Transactions, Reports, Rules |
| Household members and shared settings | Household | Rules, Accounts, Transactions |

## Function Groups

### Auth

Auth owns the session lifecycle only: create a token-backed session, save it, load it, and provide auth headers for future API calls. It should stay as the only group that knows about REST auth endpoints and `Authorization: Token ...` headers.

#### Core Functions

- `create_session(email: str, password: str, *, mfa_code: str | None = None, trusted_device: bool = True, session_path: str | Path | None = None) -> AuthSession`
- `save_session(session: AuthSession, path: str | Path) -> None`
- `load_session(path: str | Path) -> AuthSession`
- `build_auth_headers(session: AuthSession | None = None, *, graphql: bool = False) -> dict[str, str]`

#### Boundary With Household

Auth may keep lightweight identifiers returned during login, such as `user_id` and `email`. Household member management, invitations, shared settings, and subscription details belong in Household.

### Accounts

Accounts owns account records, balances, institutions, sync status, net worth, and manual account maintenance.

#### Core Functions

- `list_accounts(filters: AccountFilter | None = None) -> list[Account]`
- `get_account(account_id: AccountId) -> Account`
- `get_account_history(account_id: AccountId) -> list[AccountHistoryPoint]`
- `get_net_worth_performance(start_date: Date | None = None, end_date: Date | None = None, filters: AccountFilter | None = None) -> list[NetWorthSnapshot]`
- `get_net_worth_breakdown(start_date: Date, timeframe: str, filters: AccountFilter | None = None) -> list[NetWorthBreakdownPoint]`
- `get_historical_balances(balance_date: Date, filters: AccountFilter | None = None) -> list[AccountBalance]`
- `create_manual_account(name: str, type: str, subtype: str, balance: MoneyAmount | None = None, include_in_net_worth: bool = True, owner_user_id: UserId | None = None) -> AccountId`
- `update_account(account_id: AccountId, *, name: str | None = None, type: str | None = None, subtype: str | None = None, balance: MoneyAmount | None = None, include_in_net_worth: bool | None = None, hide_from_list: bool | None = None, hide_transactions_from_reports: bool | None = None, owner_user_id: UserId | None = None, deactivated_at: Date | str | None = None) -> Account`
- `delete_account(account_id: AccountId) -> bool`

#### Deferred Or Limited Functions

- `start_account_connection(provider: ConnectionProvider | None = None) -> AccountConnectionSession`
- `repair_account_connection(account_id: AccountId) -> AccountConnectionSession`

These are useful but may depend on provider-specific browser flows from Plaid, MX, Finicity, or Monarch's current aggregator stack.

### Transactions

Transactions owns transaction search, detail, edits, manual transactions, deletion, review status, notes, and per-transaction associations.

#### Core Functions

- `list_transactions(filters: TransactionFilter | None = None, limit: int = 100, offset: int = 0, sort: TransactionSort = TransactionSort.DATE_DESCENDING) -> TransactionPage`
- `get_transaction(transaction_id: TransactionId, redirect_posted: bool = True) -> Transaction | None`
- `create_transaction(*, account_id: AccountId, amount: MoneyAmount, date: Date, merchant_name: str, category_id: CategoryId, notes: str | None = None, owner_user_id: UserId | None = None, should_update_balance: bool | None = None) -> Transaction`
- `update_transaction(transaction_id: TransactionId, *, date: Date | None = None, amount: MoneyAmount | None = None, account_id: AccountId | None = None, merchant_name: str | None = None, category_id: CategoryId | None = None, notes: str | None = None, hide_from_reports: bool | None = None, review_status: TransactionReviewStatus | None = None, needs_review_by_user_id: UserId | None = None, owner_user_id: UserId | None = None, tag_ids: list[TagId] | None = None) -> Transaction`
- `delete_transaction(transaction_id: TransactionId) -> bool`
- `get_transaction_splits(transaction_id: TransactionId) -> TransactionSplitDetails | None`
- `update_transaction_splits(transaction_id: TransactionId, splits: list[TransactionSplitDraft]) -> TransactionSplitDetails`
- `unsplit_transaction(transaction_id: TransactionId) -> TransactionSplitDetails`

#### Build Phases

Start with read and single-transaction workflows: list, detail, create manual transaction, update, delete, tag assignment through `update_transaction`, and full-set split editing. Bulk update/delete and multi-selection are intentionally out of scope for now because those operations can affect several transaction records.

Transaction amounts follow Monarch's signed amount convention. Negative amounts are debits and positive amounts are credits.

`update_transaction_splits()` replaces the full split set. Existing split ids should be included when editing existing split rows. Omitting an existing split row removes it. Percentage-based split helpers are deferred because Monarch's backend mutation accepts concrete split amounts.

#### Non-Goals

- Transactions should not duplicate category creation; that belongs in Categories.
- Transactions should not duplicate tag creation; that belongs in Tags.
- Transactions should not own merchant cleanup or renaming at the merchant-record level; that belongs in Merchants.
- Rule creation from a transaction edit belongs in Rules.
- Cashflow totals, chart aggregates, and transaction summary cards belong in Cashflow or Reports.
- Explicit transaction-goal linking belongs in Goals, though transactions can expose goal ids/names when present.
- Receipt upload, retail sync, and attachment upload flows are deferred until after core transaction editing. The backend supports them, but they cross into file/upload handling and retail-order matching.

### Cashflow

Cashflow owns opinionated cashflow-page data: income, expenses, savings, savings rate, trend points, and category/group/merchant breakdowns. It should answer the practical cashflow questions without requiring the caller to know Monarch's chart endpoints or reproduce the visual page layout.

#### Core Functions

- `get_cashflow_summary(start_date: Date, end_date: Date, filters: CashflowFilter | None = None) -> CashflowSummary`
- `get_cashflow_trends(start_date: Date, end_date: Date, interval: CashflowInterval = CashflowInterval.MONTH, filters: CashflowFilter | None = None) -> list[CashflowTrendPoint]`
- `get_cashflow_breakdown(start_date: Date, end_date: Date, direction: CashflowBreakdownDirection, group_by: CashflowBreakdownGroup = CashflowBreakdownGroup.CATEGORY, filters: CashflowFilter | None = None) -> CashflowBreakdown`

#### Boundary With Reports

Cashflow should not own saved reports, chart presets, report export, or generic report metadata. Those belong in Reports. Cashflow can be implemented internally using the same lower-level operation as Reports, but the public surface should remain simple.

#### Deferred

- Sankey graphs and generic visual chart modes belong in Reports unless they become clearly necessary as a cashflow-specific helper.
- Share/export behavior is UI/reporting functionality and should stay out of the first Cashflow surface.
- Separate income-only and expense-only functions are unnecessary because `get_cashflow_breakdown()` already takes a direction.

### Reports

Reports owns generic transaction aggregation and saved report presets. Reports may cover cash flow, spending, and income, but should not replace the simpler Cashflow helpers.

#### Core Functions

- `get_report_data(filters: TransactionFilter | None = None, group_by: ReportGroup | list[ReportGroup] | None = ReportGroup.CATEGORY, timeframe: ReportTimeframe | None = None, sort_by: ReportSort | None = None, fill_empty_values: bool = True) -> ReportResult`
- `list_saved_reports() -> list[SavedReport]`
- `get_saved_report(report_id: ReportId) -> SavedReport | None`
- `create_saved_report(name: str, filters: TransactionFilter | None = None, group_by: ReportGroup | list[ReportGroup] | None = ReportGroup.CATEGORY, timeframe: ReportTimeframe | None = None) -> SavedReport`
- `update_saved_report(report_id: ReportId, *, name: str) -> SavedReport`
- `delete_saved_report(report_id: ReportId) -> bool`

#### Build Notes

The first Reports surface intentionally uses keyword arguments instead of a `ReportRequest` input type. A report is just a transaction filter plus grouping options.

Saved reports are exposed as saved reports even though Monarch's backend calls them report configurations. The current backend schema supports creating saved reports with filters and view dimensions, deleting saved reports, and renaming saved reports. It does not expose an update input for changing the saved filters or view; changing those requires deleting and recreating the saved report.

Chart-specific UI settings such as chart type, density, layout, and AI report generation are deferred. Saved report raw data preserves Monarch's full response for callers that need those details.

#### Boundary With Transactions

Reports should not return full transaction pages directly for drilldowns. Callers can use the same `TransactionFilter` passed to `get_report_data()` with `Transactions.list_transactions(...)`.

### Budget

Budget owns monthly budget plans, budget rows, rollover behavior, flex/category budget settings, and moving planned amounts between categories.

#### Core Functions

- `get_budget(month: YearMonth, mode: BudgetMode | None = None) -> BudgetMonth`
- `list_budget_months(start_month: YearMonth, end_month: YearMonth) -> list[BudgetMonthSummary]`
- `get_budget_summary(month: YearMonth) -> BudgetSummary`
- `get_budget_category(month: YearMonth, category_id: CategoryId) -> BudgetCategoryRow`
- `set_budget_amount(month: YearMonth, category_id: CategoryId, amount: MoneyAmount) -> BudgetCategoryRow`
- `set_budget_amounts(month: YearMonth, amounts: list[BudgetAmountInput]) -> list[BudgetCategoryRow]`
- `set_budget_rollover(category_id: CategoryId, settings: RolloverSettings) -> BudgetCategoryRow`
- `move_budget_money(input: BudgetMoveInput) -> BudgetMove`
- `copy_budget_month(source_month: YearMonth, target_month: YearMonth, options: BudgetCopyOptions | None = None) -> BudgetMonth`
- `reset_budget_month(month: YearMonth, scope: BudgetResetScope = "planned_amounts") -> BudgetMonth`
- `get_budget_settings() -> BudgetSettings`
- `update_budget_settings(patch: BudgetSettingsPatch) -> BudgetSettings`

#### Boundary With Goals

Budget may show goal contributions or goal-related rows, but creating goals, assigning accounts to goals, and linking transactions to goals belongs in Goals.

### Recurring

Recurring owns recurring streams, upcoming expected occurrences, recurring summaries, and recurring-specific filters.

#### Core Functions

- `list_recurring_streams(filters: RecurringFilter | None = None, include_pending: bool = True, include_liabilities: bool = True) -> list[RecurringStream]`
- `get_recurring_stream(recurring_id: RecurringId, include_liabilities: bool = True) -> RecurringStream | None`
- `list_recurring_occurrences(start_date: Date, end_date: Date, filters: RecurringFilter | None = None, include_liabilities: bool = True) -> list[RecurringOccurrence]`
- `get_recurring_summary(start_date: Date, end_date: Date, filters: RecurringFilter | None = None) -> RecurringSummary`
- `create_recurring_stream(merchant_id: MerchantId, *, frequency: str, amount: MoneyAmount, base_date: Date, is_active: bool = True) -> RecurringStream`
- `update_recurring_stream(recurring_id: RecurringId, *, frequency: str | None = None, amount: MoneyAmount | None = None, base_date: Date | None = None, is_active: bool | None = None) -> RecurringStream`
- `remove_recurring_stream(recurring_id: RecurringId) -> bool`

#### Build Notes

Monarch's backend calls the recurring series a stream. The public API uses that term because it cleanly separates a recurring stream, such as "Rent monthly", from recurring occurrences, such as "Rent expected on June 1".

`create_recurring_stream()` and `update_recurring_stream()` use Monarch's merchant recurrence mutation. This creates or updates merchant-backed streams. Liability-backed recurring streams do not expose the same mutation shape and are not supported by these functions.

`remove_recurring_stream()` removes the recurrence from Monarch's recurring stream list. Under the hood, Monarch marks the stream as not recurring rather than deleting a user-owned object.

#### Boundary With Transactions

Recurring should identify expected activity and recurrence metadata. Editing the underlying transaction amount, date, category, merchant, notes, tags, or split belongs in Transactions. Paycheck CRUD and liability statement payment workflows are deferred.

### Goals

Goals owns savings, debt payoff, retirement, and custom goal records; account links; contribution rules at the goal level; and goal progress.

#### Core Functions

- `list_goals(filter: GoalFilter | None = None) -> list[Goal]`
- `get_goal(goal_id: GoalId) -> Goal`
- `create_goal(input: GoalCreate) -> Goal`
- `update_goal(goal_id: GoalId, patch: GoalPatch) -> Goal`
- `delete_goal(goal_id: GoalId) -> None`
- `archive_goal(goal_id: GoalId) -> Goal`
- `restore_goal(goal_id: GoalId) -> Goal`
- `set_goal_account_links(goal_id: GoalId, links: list[GoalAccountLinkInput]) -> Goal`
- `get_goal_progress(goal_id: GoalId, as_of: Date | None = None) -> GoalProgress`
- `list_goal_transactions(goal_id: GoalId, page: PageRequest | None = None) -> Page[Transaction]`
- `link_goal_transaction(goal_id: GoalId, transaction_id: TransactionId) -> GoalTransactionLink`
- `unlink_goal_transaction(goal_id: GoalId, transaction_id: TransactionId) -> None`
- `set_goal_priority(goal_ids_in_order: list[GoalId]) -> list[Goal]`

#### Boundary With Rules

Rules may include a "link to goal" action. Goals owns the goal records and explicit transaction-goal links.

### Investments

Investments owns securities, holdings, allocation, performance, benchmarks, and manual holdings. Account balances remain owned by Accounts.

#### Core Functions

- `get_portfolio_summary(filter: InvestmentFilter | None = None) -> PortfolioSummary`
- `list_holdings(filter: HoldingFilter | None = None) -> list[Holding]`
- `get_holding(holding_id: HoldingId) -> Holding`
- `list_securities(search: str | None = None, symbols: list[str] | None = None) -> list[Security]`
- `get_security(security_id: SecurityId | None = None, symbol: str | None = None) -> Security`
- `get_asset_allocation(filter: InvestmentFilter | None = None, group_by: AllocationGroupBy = "asset_class") -> list[AssetAllocationRow]`
- `get_investment_performance(filter: InvestmentPerformanceFilter) -> InvestmentPerformanceSeries`
- `get_benchmark_performance(symbols: list[str], date_range: DateRange) -> list[BenchmarkSeries]`
- `create_manual_holding(input: ManualHoldingCreate) -> Holding`
- `update_manual_holding(holding_id: HoldingId, patch: ManualHoldingPatch) -> Holding`
- `delete_manual_holding(holding_id: HoldingId) -> None`

#### Boundary With Accounts And Transactions

- Use Accounts for investment account metadata and balances.
- Use Transactions for investment transaction rows when Monarch Labs investment transactions are enabled.
- Use Investments for positions, securities, allocation, and performance.

### Categories

Categories owns category groups, categories, display order, names, emojis, and category activation/deactivation.

#### Core Functions

- `list_categories(filters: CategoryFilter | None = None, include_disabled: bool = False) -> list[Category]`
- `list_category_groups() -> list[CategoryGroup]`
- `get_category_catalog(include_disabled: bool = False) -> CategoryCatalog`
- `get_category(category_id: CategoryId) -> Category | None`
- `get_category_group(group_id: CategoryGroupId) -> CategoryGroup | None`
- `create_category(name: str, group_id: CategoryGroupId, icon: str) -> Category`
- `update_category(category_id: CategoryId, *, name: str | None = None, group_id: CategoryGroupId | None = None, icon: str | None = None) -> Category`
- `remove_category(category_id: CategoryId, *, move_to_category_id: CategoryId | None = None) -> bool`
- `reactivate_category(category_id: CategoryId) -> Category`
- `reorder_category(category_id: CategoryId, *, group_id: CategoryGroupId, order: int) -> Category`
- `create_category_group(name: str, type: CategoryType) -> CategoryGroup`
- `update_category_group(group_id: CategoryGroupId, *, name: str | None = None, type: CategoryType | None = None) -> CategoryGroup`
- `delete_category_group(group_id: CategoryGroupId, *, move_to_group_id: CategoryGroupId | None = None) -> bool`
- `reorder_category_group(group_id: CategoryGroupId, *, order: int) -> list[CategoryGroup]`

#### Boundary With Budget

The category page exposes some budget-adjacent fields such as budget variability and budget exclusion. Those fields can be returned on `Category`, but dedicated budget planning operations belong in Budget.

#### Listing Shape

`list_categories()` only requests and returns categories. `list_category_groups()` only requests and returns groups. `get_category_catalog()` is the intentional combined view for category-page organization; it requests both resources and applies Monarch-style group/category ordering.

### Merchants

Merchants owns normalized merchant records: display names, logos, usage counts, recurring flags, and merchant cleanup operations.

#### Core Functions

- `list_merchants(search: str | None = None, limit: int | None = None, offset: int | None = None, sort: MerchantSort = MerchantSort.TRANSACTION_COUNT) -> list[Merchant]`
- `get_merchant(merchant_id: MerchantId) -> Merchant | None`
- `update_merchant(merchant_id: MerchantId, *, name: str | None = None) -> Merchant`
- `delete_merchant(merchant_id: MerchantId, *, move_to_merchant_id: MerchantId | None = None) -> bool`

#### Boundary With Transactions

Selecting a merchant for a transaction, recommended merchants for a transaction, and listing transactions for a merchant belong in Transactions. Those operations depend on transaction context or return transaction records.

There is no planned standalone `create_merchant()` function right now. The recon data shows merchant search/list/update/delete operations, and the web app exposes "create new merchant" from merchant selection UI, but no dedicated `createMerchant` mutation. If Monarch creates merchant records implicitly when a transaction is created or updated with a new merchant name, that belongs in Transactions rather than Merchants.

#### Boundary With Rules

Rules own future automatic merchant renames. Merchants owns existing merchant records and cleanup.

#### Boundary With Recurring

Merchant detail can expose whether a merchant has active recurring streams, but editing recurrence settings belongs in Recurring.

#### Deferred

Merchant logo upload/update is deferred for now. Monarch supports `setMerchantLogo` using a Cloudinary public id and `deleteMerchantLogo`, but that crosses into asset upload handling and is not needed for the first merchant surface. Merchant spending summaries are better handled by Reports.

### Rules

Rules owns transaction automation: matching criteria, actions, smart splits, order, preview, enablement, and bulk application to existing transactions.

#### Core Functions

- `list_rules(filter: RuleFilter | None = None) -> list[Rule]`
- `get_rule(rule_id: RuleId) -> Rule`
- `create_rule(input: RuleCreate) -> Rule`
- `update_rule(rule_id: RuleId, patch: RulePatch) -> Rule`
- `delete_rule(rule_id: RuleId) -> None`
- `delete_all_rules() -> None`
- `enable_rule(rule_id: RuleId) -> Rule`
- `disable_rule(rule_id: RuleId) -> Rule`
- `reorder_rules(rule_ids_in_order: list[RuleId]) -> list[Rule]`
- `preview_rule(input: RuleCreate | RulePatch, page: PageRequest | None = None) -> RulePreview`
- `apply_rule_to_existing_transactions(rule_id: RuleId, filter: TransactionFilter | None = None) -> RuleApplyJob`
- `get_rule_apply_status(job_id: str) -> RuleApplyStatus`
- `create_rule_from_transaction_edit(transaction_id: TransactionId, criteria: RuleCriteriaInput) -> Rule`

#### Rule Capabilities

Criteria should support merchant/original-statement matches, amount comparisons and ranges, categories, accounts, tags, review status, transaction type, and member/shared-view constraints when available.

Actions should support merchant rename, category update, tag add/remove/set, hide/unhide, review status, goal link, and smart split. Smart splits require an amount-equals condition when Monarch requires it.

### Tags

Tags owns household transaction tag definitions: names, colors, order, and transaction usage counts. Transaction-tag assignment belongs in Transactions because it edits a transaction.

#### Core Functions

- `list_tags(search: str | None = None, limit: int | None = None, include_transaction_count: bool = False) -> list[Tag]`
- `get_tag(tag_id: TagId) -> Tag | None`
- `create_tag(name: str, color: str) -> Tag`
- `update_tag(tag_id: TagId, *, name: str | None = None, color: str | None = None) -> Tag`
- `delete_tag(tag_id: TagId) -> bool`
- `reorder_tag(tag_id: TagId, *, order: int) -> list[Tag]`

#### Boundary With Transactions

Tags should not own transaction tag assignment. Tag assignment mutates transactions, so it belongs in `update_transaction(..., tag_ids=[...])` even though it uses `Tag` objects.

#### Deferred

No archive, restore, merge, or tag-summary functions for now. The current recon points to delete/update/reorder operations, and tag-level spending summaries are better handled by Reports or Transactions filters if we need them later.

### Household

Household owns the shared Monarch workspace record, its active member records, the current user's profile, and core shared household preferences. Invitation management, subscription details, member removal, security settings, dashboard configuration, and advisor access are deferred.

#### Core Functions

- `get_household() -> Household`
- `list_household_members() -> list[HouseholdMember]`
- `get_household_member(member_id: MemberId) -> HouseholdMember | None`
- `get_current_user() -> UserProfile`
- `update_current_user(*, display_name: str | None = None, timezone: str | None = None) -> UserProfile`
- `get_household_preferences() -> HouseholdPreferences`
- `update_household_preferences(*, new_transactions_need_review: bool | None = None, uncategorized_transactions_need_review: bool | None = None, pending_transactions_can_be_edited: bool | None = None, hidden_transactions_beta_enabled: bool | None = None, exclude_business_from_budget: bool | None = None) -> HouseholdPreferences`

#### Boundary With Accounts

Members may own or contribute accounts, but account records and balances remain in Accounts.

#### Deferred

No invitations, subscription/billing, household deletion, member removal, MFA/security, notification preferences, profile-picture upload, dashboard configuration, or advisor access functions for now.

## Shared Data Types

The exact field names should be adapted to the final Python style, but the client should expose stable typed models. Prefer `Decimal` for money, `date` for calendar dates, and timezone-aware `datetime` for timestamps.

### Common Scalar Aliases

```python
AccountId = str
TransactionId = str
CategoryId = str
CategoryGroupId = str
TagId = str
MerchantId = str
RuleId = str
GoalId = str
RecurringId = str
MemberId = str
InstitutionId = str
HoldingId = str
SecurityId = str
ReportId = str
AttachmentId = str
InviteId = str
MoneyAmount = Decimal
Date = datetime.date
DateTime = datetime.datetime
YearMonth = str  # "YYYY-MM"
```

### Common Models

```python
class AuthSession:
    token: str
    token_expiration: str | None
    user_id: str | None
    email: str | None

class DateRange:
    start_date: Date | None
    end_date: Date | None

class PageRequest:
    limit: int = 100
    offset: int = 0

class Page[T]:
    items: list[T]
    total_count: int | None
    limit: int
    offset: int
    has_more: bool

class Sort:
    field: str
    direction: Literal["asc", "desc"]

class Money:
    amount: MoneyAmount
    currency: str | None  # Monarch commonly displays USD/CAD-like "$" values without true conversion.

class FileUpload:
    filename: str
    content_type: str
    bytes: bytes

class User:
    id: UserId
    display_name: str | None
    profile_picture_url: str | None
    raw: JsonDict | None

class FieldError:
    field: str | None
    messages: list[str]

class MonarchError:
    message: str
    code: str | None
    field_errors: list[FieldError]

class BulkMutationResult[T]:
    succeeded: list[T]
    failed: list[BulkMutationFailure]

class BulkMutationFailure:
    id: str
    error: MonarchError

ReviewStatus = Literal["needs_review", "reviewed", "not_reviewed"]
```

### Accounts Types

```python
class AccountType:
    name: str | None
    display_name: str | None
    group: str | None

class Institution:
    id: InstitutionId | None
    name: str | None
    logo: str | None
    primary_color: str | None
    raw: JsonDict | None

class Account:
    id: AccountId
    display_name: str
    balance: MoneyAmount | None
    current_balance: MoneyAmount | None
    last_updated_at: DateTime | None
    type: AccountType | None
    subtype: AccountType | None
    institution: Institution | None
    owner: User | None
    is_asset: bool | None
    is_manual: bool | None
    is_hidden: bool | None
    sync_disabled: bool | None
    include_in_net_worth: bool | None
    logo_url: str | None
    icon: str | None
    raw: JsonDict | None

class AccountFilter:
    account_ids: list[AccountId] | None
    account_types: list[str] | None
    account_subtypes: list[str] | None
    groups: list[str] | None
    include_hidden: bool | None
    include_deleted: bool | None

class AccountBalance:
    account_id: AccountId
    balance: MoneyAmount | None
    include_in_net_worth: bool | None
    account_type: str | None
    raw: JsonDict | None

class AccountHistoryPoint:
    account_id: AccountId
    date: Date
    balance: MoneyAmount | None
    raw: JsonDict | None

class NetWorthBreakdownPoint:
    account_type: str
    date: Date
    balance: MoneyAmount | None
    account_group: str | None
    raw: JsonDict | None

class NetWorthSnapshot:
    date: Date
    net_worth: MoneyAmount | None
    assets_balance: MoneyAmount | None
    liabilities_balance: MoneyAmount | None
    raw: JsonDict | None

```

### Transactions Types

```python
class Transaction:
    id: TransactionId
    date: Date
    amount: MoneyAmount
    pending: bool | None
    account: AccountReference | None
    merchant: MerchantReference | None
    merchant_name: str
    original_statement: str | None
    category: CategoryReference | None
    tags: list[TagReference]
    notes: str | None
    review_status: TransactionReviewStatus | None
    needs_review: bool | None
    needs_review_by_user: User | None
    reviewed_at: DateTime | None
    reviewed_by_user: User | None
    hide_from_reports: bool | None
    hidden_by_account: bool | None
    is_split: bool | None
    has_splits: bool | None
    is_recurring: bool | None
    recurring_id: str | None
    goal: GoalReference | None
    original_transaction_id: str | None
    attachment_count: int
    owner: User | None
    is_manual: bool | None
    synced_from_institution: bool | None
    imported_from_mint: bool | None
    deleted_at: DateTime | None
    updated_at: DateTime | None
    raw: JsonDict | None

class TransactionFilter:
    start_date: Date | None
    end_date: Date | None
    search: str | None
    transaction_ids: list[TransactionId] | None
    account_ids: list[AccountId] | None
    category_ids: list[CategoryId] | None
    category_group_ids: list[CategoryGroupId] | None
    merchant_ids: list[MerchantId] | None
    tag_ids: list[TagId] | None
    goal_ids: list[GoalId] | None
    min_absolute_amount: MoneyAmount | None
    max_absolute_amount: MoneyAmount | None
    category_type: CategoryType | None
    credits_only: bool | None
    debits_only: bool | None
    is_pending: bool | None
    is_recurring: bool | None
    is_split: bool | None
    is_uncategorized: bool | None
    is_untagged: bool | None
    has_notes: bool | None
    has_attachments: bool | None
    hide_from_reports: bool | None
    needs_review: bool | None
    needs_review_by_user_id: UserId | None
    needs_review_unassigned: bool | None
    synced_from_institution: bool | None
    imported_from_mint: bool | None
    transaction_visibility: TransactionVisibility | None

class TransactionSort(str, Enum):
    DATE_DESCENDING = "date"
    DATE_ASCENDING = "inverse_date"
    AMOUNT_DESCENDING = "amount"
    AMOUNT_ASCENDING = "inverse_amount"

class TransactionReviewStatus(str, Enum):
    REVIEWED = "reviewed"
    NEEDS_REVIEW = "needs_review"

class TransactionVisibility(str, Enum):
    ALL = "all_transactions"
    VISIBLE_ONLY = "non_hidden_transactions_only"
    HIDDEN_ONLY = "hidden_transactions_only"

class TransactionPage:
    transactions: list[Transaction]
    total_count: int
    limit: int
    offset: int

class AccountReference:
    id: AccountId
    display_name: str
    logo_url: str | None
    icon: str | None
    raw: JsonDict | None

class MerchantReference:
    id: MerchantId
    name: str
    logo_url: str | None
    transaction_count: int | None
    recurring_id: str | None
    raw: JsonDict | None

class CategoryReference:
    id: CategoryId
    name: str
    icon: str | None
    group_id: CategoryGroupId | None
    type: CategoryType | None
    raw: JsonDict | None

class TagReference:
    id: TagId
    name: str
    color: str | None
    order: int | None
    raw: JsonDict | None

class GoalReference:
    id: GoalId
    name: str | None
    raw: JsonDict | None

class TransactionSplit:
    id: TransactionId
    amount: MoneyAmount
    date: Date | None
    merchant: MerchantReference | None
    merchant_name: str
    category: CategoryReference | None
    goal: GoalReference | None
    tags: list[TagReference]
    notes: str | None
    hide_from_reports: bool | None
    review_status: TransactionReviewStatus | None
    needs_review: bool | None
    needs_review_by_user: User | None
    owner: User | None
    raw: JsonDict | None

class TransactionSplitDetails:
    transaction: Transaction
    splits: list[TransactionSplit]

class TransactionSplitDraft:
    amount: MoneyAmount
    id: TransactionId | None
    date: Date | None
    merchant_name: str | None
    category_id: CategoryId | None
    notes: str | None
    hide_from_reports: bool | None
    review_status: TransactionReviewStatus | None
    needs_review: bool | None
    needs_review_by_user_id: UserId | None
    owner_user_id: UserId | None
    tag_ids: list[TagId] | None
    goal_id: GoalId | None

```

### Cashflow Types

```python
class CashflowInterval(str, Enum):
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class CashflowBreakdownDirection(str, Enum):
    INCOME = "income"
    EXPENSES = "expenses"

class CashflowBreakdownGroup(str, Enum):
    CATEGORY = "category"
    CATEGORY_GROUP = "category_group"
    MERCHANT = "merchant"

class CashflowFilter:
    account_ids: list[str] | None
    category_ids: list[str] | None
    category_group_ids: list[str] | None
    merchant_ids: list[str] | None
    tag_ids: list[str] | None
    include_hidden: bool = False

class CashflowSummary:
    start_date: str
    end_date: str
    income: float
    expenses: float
    savings: float
    savings_rate: float | None
    raw: JsonDict | None

class CashflowTrendPoint:
    start_date: str
    end_date: str
    label: str | None
    income: float
    expenses: float
    savings: float
    savings_rate: float | None
    raw: JsonDict | None

class CashflowBreakdownRow:
    id: str | None
    name: str
    amount: float
    percent: float | None
    transaction_count: int | None
    category: CategoryReference | None
    category_group: CategoryGroupReference | None
    merchant: MerchantReference | None
    raw: JsonDict | None

class CashflowBreakdown:
    direction: CashflowBreakdownDirection
    group_by: CashflowBreakdownGroup
    rows: list[CashflowBreakdownRow]
```

Cashflow summary values use positive numbers for both `income` and `expenses` because they model reporting totals rather than raw signed transaction rows. `savings` may be negative. Breakdown row `amount` values are signed within the selected direction, so negative income adjustments or expense refunds can appear as negative rows.

### Reports Types

```python
class ReportGroup(str, Enum):
    CATEGORY = "category"
    CATEGORY_GROUP = "category_group"
    MERCHANT = "merchant"

class ReportTimeframe(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class ReportSort(str, Enum):
    TOTAL = "sum"
    INCOME = "sum_income"
    EXPENSES = "sum_expense"
    COUNT = "count"
    AVERAGE = "avg"
    MAX = "max"

class ReportResult:
    summary: ReportSummary
    rows: list[ReportRow]
    raw: JsonDict | None

class ReportRow:
    group: ReportGroupValue
    summary: ReportSummary
    raw: JsonDict | None

class ReportGroupValue:
    date: str | None
    category: CategoryReference | None
    category_group: CategoryGroupReference | None
    merchant: MerchantReference | None
    raw: JsonDict | None

class ReportSummary:
    total: float | None
    average: float | None
    count: int | None
    max: float | None
    income: float | None
    expenses: float | None
    savings: float | None
    savings_rate: float | None
    first_date: str | None
    last_date: str | None
    raw: JsonDict | None

class SavedReport:
    id: ReportId
    name: str
    filters: TransactionFilter | None
    group_by: list[ReportGroup] | None
    timeframe: ReportTimeframe | None
    raw: JsonDict | None
```

### Budget Types

```python
BudgetMode = Literal["category", "flex"]

class BudgetMonth:
    month: YearMonth
    mode: BudgetMode
    summary: BudgetSummary
    groups: list[BudgetGroupRow]

class BudgetMonthSummary:
    month: YearMonth
    planned_income: MoneyAmount
    actual_income: MoneyAmount
    planned_expenses: MoneyAmount
    actual_expenses: MoneyAmount
    remaining: MoneyAmount

class BudgetSummary:
    month: YearMonth
    planned_income: MoneyAmount
    actual_income: MoneyAmount
    planned_expenses: MoneyAmount
    actual_expenses: MoneyAmount
    planned_savings: MoneyAmount
    actual_savings: MoneyAmount
    remaining_to_budget: MoneyAmount

class BudgetGroupRow:
    group: CategoryGroupReference
    planned: MoneyAmount
    actual: MoneyAmount
    remaining: MoneyAmount
    categories: list[BudgetCategoryRow]

class BudgetCategoryRow:
    category: CategoryReference
    planned: MoneyAmount
    actual: MoneyAmount
    remaining: MoneyAmount
    rollover: RolloverState | None
    goal_id: GoalId | None

class BudgetAmountInput:
    category_id: CategoryId
    amount: MoneyAmount

class RolloverSettings:
    enabled: bool
    type: Literal["monthly", "annual", "custom"] | None
    start_month: YearMonth | None
    starting_balance: MoneyAmount | None

class RolloverState:
    enabled: bool
    balance: MoneyAmount
    carried_from_prior_month: MoneyAmount

class BudgetMoveInput:
    month: YearMonth
    from_category_id: CategoryId | None
    to_category_id: CategoryId
    amount: MoneyAmount
    note: str | None

class BudgetMove:
    id: str
    month: YearMonth
    from_category_id: CategoryId | None
    to_category_id: CategoryId
    amount: MoneyAmount
    created_at: DateTime

BudgetResetScope = Literal["planned_amounts", "rollovers", "all"]

class BudgetCopyOptions:
    copy_planned_amounts: bool = True
    copy_rollover_settings: bool = True
    overwrite_existing: bool = False

class BudgetSettings:
    mode: BudgetMode
    start_month: YearMonth | None
    include_goals: bool | None
    flex_settings: FlexBudgetSettings | None

class FlexBudgetSettings:
    fixed_category_group_ids: list[CategoryGroupId]
    non_monthly_category_group_ids: list[CategoryGroupId]
    flexible_category_group_ids: list[CategoryGroupId]

class BudgetSettingsPatch:
    mode: BudgetMode | None
    include_goals: bool | None
    flex_settings: FlexBudgetSettings | None
```

### Recurring Types

```python
class RecurringFrequency(str, Enum):
    WEEKLY = "weekly"
    EVERY_TWO_WEEKS = "every_two_weeks"
    TWICE_A_MONTH = "twice_a_month"
    MONTHLY = "monthly"
    EVERY_TWO_MONTHS = "every_two_months"
    QUARTERLY = "quarterly"
    EVERY_SIX_MONTHS = "every_six_months"
    YEARLY = "yearly"

class RecurringType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    CREDIT_CARD = "credit_card"

class RecurringStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    IGNORED = "ignored"

class RecurringFilter:
    account_ids: list[AccountId] | None
    category_ids: list[CategoryId] | None
    merchant_ids: list[MerchantId] | None
    recurring_ids: list[RecurringId] | None
    frequencies: list[RecurringFrequency | str] | None
    recurring_types: list[RecurringType | str] | None
    is_completed: bool | None

class RecurringStream:
    id: RecurringId
    name: str
    frequency: str | None
    amount: float | None
    next_date: str | None
    next_amount: float | None
    base_date: str | None
    day_of_month: int | None
    is_active: bool | None
    is_approximate: bool | None
    recurring_type: RecurringType | None
    status: RecurringStatus | None
    merchant: MerchantReference | None
    account: AccountReference | None
    category: CategoryReference | None
    liability_account_id: AccountId | None
    raw: JsonDict | None

class RecurringOccurrence:
    recurring_id: RecurringId
    date: str
    amount: float | None
    name: str
    frequency: str | None
    merchant: MerchantReference | None
    account: AccountReference | None
    category: CategoryReference | None
    transaction_id: TransactionId | None
    is_past: bool | None
    is_late: bool | None
    is_completed: bool | None
    marked_paid_at: str | None
    raw: JsonDict | None

class RecurringSummary:
    expense: RecurringSummaryBucket
    income: RecurringSummaryBucket
    credit_card: RecurringSummaryBucket
    raw: JsonDict | None

class RecurringSummaryBucket:
    completed: float | None
    remaining: float | None
    total: float | None
    count: int | None
    pending_amount_count: int | None
    raw: JsonDict | None
```

### Goals Types

```python
GoalType = Literal["save_up", "pay_down", "retirement", "custom"]
GoalStatus = Literal["active", "archived", "completed"]

class GoalFilter:
    statuses: list[GoalStatus] | None
    types: list[GoalType] | None
    account_ids: list[AccountId] | None
    search: str | None

class Goal:
    id: GoalId
    name: str
    type: GoalType
    status: GoalStatus
    target_amount: MoneyAmount | None
    current_amount: MoneyAmount
    target_date: Date | None
    monthly_contribution: MoneyAmount | None
    priority: int | None
    accounts: list[GoalAccountLink]
    created_at: DateTime | None
    updated_at: DateTime | None

class GoalCreate:
    name: str
    type: GoalType
    target_amount: MoneyAmount | None
    target_date: Date | None
    monthly_contribution: MoneyAmount | None
    account_links: list[GoalAccountLinkInput] | None

class GoalPatch:
    name: str | None
    target_amount: MoneyAmount | None
    target_date: Date | None
    monthly_contribution: MoneyAmount | None
    status: GoalStatus | None

class GoalAccountLink:
    account: AccountReference
    allocation_amount: MoneyAmount | None
    allocation_percent: Decimal | None

class GoalAccountLinkInput:
    account_id: AccountId
    allocation_amount: MoneyAmount | None
    allocation_percent: Decimal | None

class GoalProgress:
    goal_id: GoalId
    current_amount: MoneyAmount
    target_amount: MoneyAmount | None
    remaining_amount: MoneyAmount | None
    progress_percent: Decimal | None
    projected_completion_date: Date | None

class GoalTransactionLink:
    goal_id: GoalId
    transaction_id: TransactionId
    linked_at: DateTime
```

### Investments Types

```python
class Security:
    id: SecurityId
    symbol: str | None
    name: str
    type: Literal["stock", "etf", "mutual_fund", "fixed_income", "crypto", "cash", "option", "other"]
    exchange: str | None
    currency: str | None
    latest_price: MoneyAmount | None
    latest_price_at: DateTime | None

class Holding:
    id: HoldingId
    account: AccountReference
    security: Security
    quantity: Decimal
    price: MoneyAmount | None
    market_value: MoneyAmount
    cost_basis: MoneyAmount | None
    day_change_amount: MoneyAmount | None
    day_change_percent: Decimal | None
    total_return_amount: MoneyAmount | None
    total_return_percent: Decimal | None
    is_manual: bool
    updated_at: DateTime | None

class HoldingFilter:
    account_ids: list[AccountId] | None
    security_ids: list[SecurityId] | None
    symbols: list[str] | None
    asset_types: list[str] | None
    manual_only: bool | None

class InvestmentFilter:
    account_ids: list[AccountId] | None
    security_ids: list[SecurityId] | None
    asset_types: list[str] | None

AllocationGroupBy = Literal["asset_class", "account", "security", "sector"]

class PortfolioSummary:
    total_value: MoneyAmount
    day_change_amount: MoneyAmount | None
    day_change_percent: Decimal | None
    total_return_amount: MoneyAmount | None
    total_return_percent: Decimal | None
    holdings_count: int

class AssetAllocationRow:
    key: str
    label: str
    market_value: MoneyAmount
    percent_of_portfolio: Decimal

class InvestmentPerformanceFilter:
    date_range: DateRange
    account_ids: list[AccountId] | None
    security_ids: list[SecurityId] | None
    benchmark_symbols: list[str] | None

class InvestmentPerformanceSeries:
    portfolio: list[InvestmentPerformancePoint]
    benchmarks: list[BenchmarkSeries]

class InvestmentPerformancePoint:
    date: Date
    value: MoneyAmount
    return_percent: Decimal | None

class BenchmarkSeries:
    symbol: str
    points: list[InvestmentPerformancePoint]

class ManualHoldingCreate:
    account_id: AccountId
    security_id: SecurityId | None
    symbol: str | None
    quantity: Decimal
    cost_basis: MoneyAmount | None

class ManualHoldingPatch:
    quantity: Decimal | None
    cost_basis: MoneyAmount | None
```

### Categories Types

```python
class CategoryType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"

class CategoryGroupReference:
    id: CategoryGroupId
    name: str | None
    type: CategoryType | None
    raw: JsonDict | None

class CategoryGroup:
    id: CategoryGroupId
    name: str
    type: CategoryType | None
    order: int | None
    color: str | None
    group_level_budgeting_enabled: bool | None
    budget_variability: str | None
    raw: JsonDict | None

class Category:
    id: CategoryId
    name: str
    icon: str | None
    order: int | None
    group: CategoryGroupReference | None
    type: CategoryType | None
    system_category: str | None
    system_category_display_name: str | None
    is_system: bool | None
    is_disabled: bool | None
    is_protected: bool | None
    exclude_from_budget: bool | None
    budget_variability: str | None
    raw: JsonDict | None

class CategoryFilter:
    group_ids: list[CategoryGroupId] | None
    types: list[CategoryType] | None

class CategoryCatalog:
    groups: list[CategoryGroup]
    categories: list[Category]
```

### Merchants Types

```python
class Merchant:
    id: MerchantId
    name: str
    logo_url: str | None
    transaction_count: int | None
    rule_count: int | None
    can_be_deleted: bool | None
    recurring_id: str | None
    created_at: str | None
    raw: JsonDict | None

class MerchantSort(str, Enum):
    NAME = "NAME"
    TRANSACTION_COUNT = "TRANSACTION_COUNT"
```

### Rules Types

```python
class Rule:
    id: RuleId
    name: str | None
    enabled: bool
    order: int
    criteria: RuleCriteria
    actions: list[RuleAction]
    apply_to_existing: bool | None
    created_by: MemberReference | None
    created_at: DateTime | None
    updated_at: DateTime | None

class RuleCreate:
    name: str | None
    enabled: bool = True
    criteria: RuleCriteria
    actions: list[RuleAction]
    position: int | None
    apply_to_existing: bool = False

class RulePatch:
    name: str | None
    enabled: bool | None
    criteria: RuleCriteria | None
    actions: list[RuleAction] | None
    position: int | None

class RuleCriteria:
    merchant: TextMatch | None
    original_statement: TextMatch | None
    amount: AmountCriterion | None
    category_ids: list[CategoryId] | None
    account_ids: list[AccountId] | None
    tag_ids: list[TagId] | None
    transaction_types: list[str] | None
    member_ids: list[MemberId] | None

RuleCriteriaInput = RuleCriteria

class TextMatch:
    operator: Literal["equals", "contains", "starts_with", "ends_with", "regex"]
    value: str
    case_sensitive: bool = False

class AmountCriterion:
    operator: Literal["eq", "gt", "gte", "lt", "lte", "between"]
    amount: MoneyAmount | None
    min_amount: MoneyAmount | None
    max_amount: MoneyAmount | None
    direction: Literal["debit", "credit"] | None

class RuleAction:
    type: Literal["rename_merchant", "set_category", "add_tags", "remove_tags", "set_tags", "hide", "unhide", "set_review_status", "link_goal", "split"]
    merchant_name: str | None
    category_id: CategoryId | None
    tag_ids: list[TagId] | None
    hidden_from_reports: bool | None
    review_status: ReviewStatus | None
    goal_id: GoalId | None
    splits: list[RuleSplitInput] | None

class RuleSplitInput:
    type: Literal["amount", "percent"]
    amount: MoneyAmount | None
    percent: Decimal | None
    category_id: CategoryId | None
    merchant_name: str | None
    notes: str | None
    tag_ids: list[TagId] | None

class RuleFilter:
    enabled: bool | None
    search: str | None
    references_account_id: AccountId | None
    references_category_id: CategoryId | None
    references_tag_id: TagId | None
    references_goal_id: GoalId | None

class RulePreview:
    matched_count: int
    sample_transactions: list[Transaction]
    proposed_changes: list[RulePreviewChange]

class RulePreviewChange:
    transaction_id: TransactionId
    before: Transaction
    after: Transaction

class RuleApplyJob:
    id: str
    rule_id: RuleId
    matched_count: int | None
    started_at: DateTime

class RuleApplyStatus:
    job_id: str
    status: Literal["queued", "running", "complete", "failed"]
    changed_count: int | None
    error: MonarchError | None
```

### Tags Types

```python
class Tag:
    id: TagId
    name: str
    color: str | None
    order: int | None
    transaction_count: int | None
    raw: JsonDict | None
```

### Household Types

```python
class Household:
    id: str
    name: str | None
    address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    country: str | None
    raw: JsonDict | None

class HouseholdMember:
    id: MemberId
    name: str | None
    display_name: str | None
    email: str | None
    role: HouseholdRole | None
    has_mfa_on: bool | None
    profile_picture_url: str | None
    raw: JsonDict | None

HouseholdRole = Literal["owner", "manager", "member", "advisor"]

class UserProfile:
    id: MemberId
    email: str | None
    name: str | None
    display_name: str | None
    timezone: str | None
    household_role: HouseholdRole | None
    has_password: bool | None
    has_mfa_on: bool | None
    is_superuser: bool | None
    profile_picture_url: str | None
    created_at: str | None
    pending_email_update: str | None
    raw: JsonDict | None

class HouseholdPreferences:
    id: str
    new_transactions_need_review: bool | None
    uncategorized_transactions_need_review: bool | None
    pending_transactions_can_be_edited: bool | None
    account_group_order: list[str] | None
    ai_assistant_enabled: bool | None
    llm_enrichment_enabled: bool | None
    investment_transactions_enabled: bool | None
    budget_apply_to_future_months_default: bool | None
    hidden_transactions_beta_enabled: bool | None
    collaboration_tools_enabled: bool | None
    agg_data_sharing_enabled: bool | None
    ai_model_training_on_user_data_enabled: bool | None
    exclude_business_from_budget: bool | None
    continuous_financial_monitoring_enabled: bool | None
    eligible_for_financial_insights: bool | None
    budget_system: str | None
    raw: JsonDict | None
```

### Lightweight Reference Types

Use reference types inside larger models to avoid pulling full object graphs everywhere.

```python
class AccountReference:
    id: AccountId
    display_name: str
    type: str | None
    subtype: str | None

class CategoryReference:
    id: CategoryId
    name: str
    icon: str | None
    group_id: CategoryGroupId | None
    type: CategoryType | None

class CategoryGroupReference:
    id: CategoryGroupId
    name: str
    type: CategoryType | None

class TagReference:
    id: TagId
    name: str
    color: str | None

class MerchantReference:
    id: MerchantId | None
    name: str
    logo_url: str | None

class GoalReference:
    id: GoalId
    name: str | None

class MemberReference:
    id: MemberId
    display_name: str
    email: str | None
```

## Recommended Implementation Order

1. Auth login/session support, MFA challenge handling, logout, current-user lookup, and password flows.
2. Accounts read functions, manual accounts, balances, and net worth history.
3. Categories, Tags, and Merchants metadata functions.
4. Transactions list/detail/create/update/delete with tag assignment handled by `update_transaction` and the core `TransactionFilter`.
5. Cashflow summary and breakdown.
6. Budget read and planned amount updates.
7. Recurring read functions.
8. Rules CRUD, preview, order, and apply-to-existing.
9. Goals CRUD and transaction links.
10. Investments holdings, allocation, and performance.
11. Reports and saved reports.
12. Household workspace, active members, current-user profile, and core preferences.

## Source Notes

This plan is based on Monarch's public help documentation for current web-app functionality and on community API surfaces used as hints for feasible operations:

- Monarch help: [Default Categories](https://help.monarch.com/hc/en-us/articles/360048883851-Default-Categories), [Budget](https://help.monarchmoney.com/hc/en-us/articles/360048883631-Budget), [Using Goals](https://help.monarchmoney.com/hc/en-us/articles/15000751305108-Using-Goals), [Using Reports](https://help.monarch.com/hc/en-us/articles/21846787088916-Using-Reports), [Cash Flow](https://help.monarchmoney.com/hc/en-us/articles/20504904768020-Cash-Flow), [Creating Transaction Rules](https://help.monarch.com/hc/en-us/articles/360048393372-Creating-Transaction-Rules), [Hiding or Unhiding Transactions](https://help.monarch.com/hc/en-us/articles/4405041904916-Hiding-or-Unhiding-Transactions), [Investments in Monarch](https://help.monarch.com/hc/en-us/articles/41855507661076-Investments-in-Monarch), [Manual Investment Holdings](https://help.monarchmoney.com/hc/en-us/articles/10032888165140-Manual-Investment-Holdings), and [Add Members to an Existing Account](https://help.monarchmoney.com/hc/en-us/articles/360048393452-Add-Members-to-an-Existing-Account).
- Community clients: [hammem/monarchmoney](https://github.com/hammem/monarchmoney) and [pbassham/monarch-money-api](https://github.com/pbassham/monarch-money-api).

Because Monarch does not publish a stable public API contract, every implementation should expect GraphQL operation names, fields, and auth behavior to change.
