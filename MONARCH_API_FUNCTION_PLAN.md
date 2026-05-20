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

- `list_accounts(filter: AccountFilter | None = None) -> list[Account]`
- `get_account(account_id: AccountId) -> Account`
- `get_account_history(account_id: AccountId) -> list[AccountHistoryPoint]`
- `get_net_worth_performance(start_date: Date | None = None, end_date: Date | None = None, account_filter: AccountFilter | None = None) -> list[NetWorthSnapshot]`
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

Transactions owns transaction search, detail, edits, splits, manual transactions, deletion, review status, notes, attachments, and per-transaction associations.

#### Core Functions

- `list_transactions(filter: TransactionFilter | None = None, page: PageRequest | None = None, sort: TransactionSort | None = None) -> Page[Transaction]`
- `get_transaction(transaction_id: TransactionId, include_splits: bool = True) -> Transaction`
- `get_transaction_summary(filter: TransactionFilter | None = None) -> TransactionSummary`
- `create_transaction(input: TransactionCreate) -> Transaction`
- `update_transaction(transaction_id: TransactionId, patch: TransactionPatch) -> Transaction`
- `bulk_update_transactions(transaction_ids: list[TransactionId], patch: TransactionPatch) -> BulkMutationResult[Transaction]`
- `delete_transaction(transaction_id: TransactionId) -> None`
- `bulk_delete_transactions(transaction_ids: list[TransactionId]) -> BulkMutationResult[None]`
- `split_transaction(transaction_id: TransactionId, splits: list[TransactionSplitInput]) -> Transaction`
- `update_transaction_splits(transaction_id: TransactionId, splits: list[TransactionSplitInput]) -> Transaction`
- `unsplit_transaction(transaction_id: TransactionId) -> Transaction`
- `list_transaction_splits(transaction_id: TransactionId) -> list[TransactionSplit]`
- `hide_transaction(transaction_id: TransactionId) -> Transaction`
- `unhide_transaction(transaction_id: TransactionId) -> Transaction`
- `set_transaction_review_status(transaction_id: TransactionId, status: ReviewStatus, reviewer_id: MemberId | None = None) -> Transaction`
- `set_transaction_tags(transaction_id: TransactionId, tag_ids: list[TagId]) -> Transaction`
- `add_transaction_note(transaction_id: TransactionId, note: str) -> Transaction`
- `clear_transaction_note(transaction_id: TransactionId) -> Transaction`
- `list_transaction_attachments(transaction_id: TransactionId) -> list[TransactionAttachment]`
- `add_transaction_attachment(transaction_id: TransactionId, file: FileUpload) -> TransactionAttachment`
- `delete_transaction_attachment(transaction_id: TransactionId, attachment_id: AttachmentId) -> None`
- `link_transaction_to_goal(transaction_id: TransactionId, goal_id: GoalId) -> Transaction`
- `unlink_transaction_from_goal(transaction_id: TransactionId) -> Transaction`

#### Non-Goals

- Category creation belongs in Categories.
- Tag creation belongs in Tags.
- Merchant merging/renaming at the merchant record level belongs in Merchants.
- Rule creation from a transaction edit belongs in Rules.

### Cashflow

Cashflow owns opinionated cashflow-page data: income, expenses, savings, saving rate, and breakdowns by category group, category, merchant, account, or tag. It should return data ready for custom dashboards without requiring the caller to know Monarch's chart endpoints.

#### Core Functions

- `get_cashflow_summary(filter: CashflowFilter) -> CashflowSummary`
- `get_cashflow_breakdown(filter: CashflowFilter, group_by: CashflowGroupBy = "category") -> list[CashflowBreakdownRow]`
- `get_cashflow_trends(filter: CashflowFilter, interval: TimeInterval = "month", group_by: CashflowGroupBy | None = None) -> list[CashflowTrendPoint]`
- `get_cashflow_sankey(filter: CashflowFilter, group_by: CashflowGroupBy = "category_group") -> SankeyGraph`
- `get_savings_rate(filter: CashflowFilter, interval: TimeInterval = "month") -> list[SavingsRatePoint]`

#### Boundary With Reports

Cashflow should not own saved reports, chart presets, report export, or generic report metadata. Those belong in Reports. Cashflow can be implemented internally using the same lower-level operation as Reports, but the public surface should remain simple.

### Reports

Reports owns generic report execution, saved reports, chart-oriented options, and report drilldowns. Reports may cover cash flow, spending, and income, but should not replace the simpler Cashflow helpers.

#### Core Functions

- `run_report(request: ReportRequest) -> ReportResult`
- `list_saved_reports() -> list[SavedReport]`
- `get_saved_report(report_id: ReportId) -> SavedReport`
- `create_saved_report(input: SavedReportCreate) -> SavedReport`
- `update_saved_report(report_id: ReportId, patch: SavedReportPatch) -> SavedReport`
- `delete_saved_report(report_id: ReportId) -> None`
- `export_report(report_id: ReportId | None = None, request: ReportRequest | None = None, format: ExportFormat = "csv") -> ReportExport`
- `get_report_drilldown_filter(request: ReportRequest, selection: ReportSelection) -> TransactionFilter`

#### Boundary With Transactions

Reports should not return full transaction pages directly for drilldowns. It should return a `TransactionFilter` that can be passed to `Transactions.list_transactions(...)`.

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

Recurring owns recurring merchant/series records, upcoming expected transactions, recurring detection metadata, and recurring-specific filters.

#### Core Functions

- `list_recurring_items(filter: RecurringFilter | None = None) -> list[RecurringItem]`
- `get_recurring_item(recurring_id: RecurringId) -> RecurringItem`
- `list_upcoming_recurring_transactions(filter: RecurringFilter | None = None) -> list[RecurringOccurrence]`
- `get_recurring_calendar(start_date: Date, end_date: Date, filter: RecurringFilter | None = None) -> list[RecurringCalendarDay]`
- `mark_transaction_recurring(transaction_id: TransactionId, input: RecurringCreateFromTransaction) -> RecurringItem`
- `update_recurring_item(recurring_id: RecurringId, patch: RecurringPatch) -> RecurringItem`
- `delete_recurring_item(recurring_id: RecurringId) -> None`
- `ignore_recurring_item(recurring_id: RecurringId) -> RecurringItem`
- `restore_recurring_item(recurring_id: RecurringId) -> RecurringItem`

#### Boundary With Transactions

Recurring should identify expected activity and recurrence metadata. Editing the underlying transaction amount, date, category, merchant, notes, tags, or split belongs in Transactions.

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

Categories owns category groups, categories, display order, names, emojis, rollover configuration defaults, and activation/deactivation.

#### Core Functions

- `list_category_groups(include_inactive: bool = False) -> list[CategoryGroup]`
- `list_categories(filter: CategoryFilter | None = None) -> list[Category]`
- `get_category(category_id: CategoryId) -> Category`
- `get_category_tree(include_inactive: bool = False) -> CategoryTree`
- `create_category_group(input: CategoryGroupCreate) -> CategoryGroup`
- `update_category_group(group_id: CategoryGroupId, patch: CategoryGroupPatch) -> CategoryGroup`
- `delete_category_group(group_id: CategoryGroupId, reassignment_group_id: CategoryGroupId | None = None) -> None`
- `reorder_category_groups(group_ids_in_order: list[CategoryGroupId]) -> list[CategoryGroup]`
- `create_category(input: CategoryCreate) -> Category`
- `update_category(category_id: CategoryId, patch: CategoryPatch) -> Category`
- `move_category(category_id: CategoryId, group_id: CategoryGroupId, position: int | None = None) -> Category`
- `reorder_categories(group_id: CategoryGroupId, category_ids_in_order: list[CategoryId]) -> list[Category]`
- `deactivate_category(category_id: CategoryId, replacement_category_id: CategoryId | None = None) -> Category`
- `reactivate_category(category_id: CategoryId) -> Category`
- `delete_category(category_id: CategoryId, replacement_category_id: CategoryId | None = None) -> None`
- `bulk_delete_categories(category_ids: list[CategoryId], replacement_category_id: CategoryId | None = None) -> BulkMutationResult[None]`

#### Boundary With Budget

Category rollover eligibility and defaults can live here, but month-specific planned, actual, remaining, and rollover values belong in Budget.

### Merchants

Merchants owns normalized merchant records, aliases, logos, merchant-level stats, and merchant cleanup operations.

#### Core Functions

- `list_merchants(filter: MerchantFilter | None = None, page: PageRequest | None = None) -> Page[Merchant]`
- `search_merchants(query: str, limit: int = 20) -> list[Merchant]`
- `get_merchant(merchant_id: MerchantId) -> Merchant`
- `get_merchant_summary(merchant_id: MerchantId, filter: TransactionFilter | None = None) -> MerchantSummary`
- `update_merchant(merchant_id: MerchantId, patch: MerchantPatch) -> Merchant`
- `merge_merchants(source_merchant_ids: list[MerchantId], target_merchant_id: MerchantId) -> Merchant`
- `list_merchant_transactions(merchant_id: MerchantId, filter: TransactionFilter | None = None, page: PageRequest | None = None) -> Page[Transaction]`

#### Boundary With Rules

Rules own future automatic merchant renames. Merchants owns existing merchant records and cleanup.

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
- `create_rule_from_transaction_edit(transaction_id: TransactionId, edit: TransactionPatch, criteria: RuleCriteriaInput) -> Rule`

#### Rule Capabilities

Criteria should support merchant/original-statement matches, amount comparisons and ranges, categories, accounts, tags, review status, transaction type, and member/shared-view constraints when available.

Actions should support merchant rename, category update, tag add/remove/set, hide/unhide, review status, goal link, and smart split. Smart splits require an amount-equals condition when Monarch requires it.

### Tags

Tags owns tag definitions. Transaction-tag assignment belongs in Transactions because it edits a transaction.

#### Core Functions

- `list_tags(include_archived: bool = False) -> list[Tag]`
- `search_tags(query: str, limit: int = 20) -> list[Tag]`
- `get_tag(tag_id: TagId) -> Tag`
- `create_tag(input: TagCreate) -> Tag`
- `update_tag(tag_id: TagId, patch: TagPatch) -> Tag`
- `delete_tag(tag_id: TagId) -> None`
- `archive_tag(tag_id: TagId) -> Tag`
- `restore_tag(tag_id: TagId) -> Tag`
- `merge_tags(source_tag_ids: list[TagId], target_tag_id: TagId) -> Tag`
- `get_tag_summary(tag_id: TagId, filter: TransactionFilter | None = None) -> TagSummary`

### Household

Household owns member records, invitations, shared household settings, subscription details, and user profile data relevant to the shared Monarch workspace.

#### Core Functions

- `get_household() -> Household`
- `list_household_members() -> list[HouseholdMember]`
- `get_household_member(member_id: MemberId) -> HouseholdMember`
- `invite_household_member(email: str, role: HouseholdRole = "member") -> HouseholdInvite`
- `list_household_invites() -> list[HouseholdInvite]`
- `resend_household_invite(invite_id: InviteId) -> HouseholdInvite`
- `revoke_household_invite(invite_id: InviteId) -> None`
- `remove_household_member(member_id: MemberId) -> None`
- `get_current_user() -> UserProfile`
- `update_current_user(patch: UserProfilePatch) -> UserProfile`
- `get_household_preferences() -> HouseholdPreferences`
- `update_household_preferences(patch: HouseholdPreferencesPatch) -> HouseholdPreferences`
- `get_subscription_details() -> SubscriptionDetails`

#### Boundary With Accounts

Members may own or contribute accounts, but account records and balances remain in Accounts.

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
    ids: list[AccountId] | None
    account_type: str | None
    account_types: list[str] | None
    account_subtype: str | None
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
    posted_at: DateTime | None
    authorized_at: DateTime | None
    amount: MoneyAmount
    direction: Literal["debit", "credit"] | None
    type: Literal["income", "expense", "transfer", "investment", "unknown"]
    account: AccountRef
    merchant: MerchantRef | None
    merchant_name: str
    original_statement: str | None
    category: CategoryRef | None
    tags: list[TagRef]
    notes: str | None
    pending: bool
    pending_transaction_id: TransactionId | None
    reviewed: bool
    needs_review: bool
    reviewer: MemberRef | None
    hidden_from_reports: bool
    is_split: bool
    parent_transaction_id: TransactionId | None
    splits: list[TransactionSplit]
    is_recurring: bool
    recurring_id: RecurringId | None
    goal_id: GoalId | None
    has_attachments: bool
    attachments: list[TransactionAttachment] | None
    synced_from_institution: bool | None
    imported_from_mint: bool | None
    created_at: DateTime | None
    updated_at: DateTime | None

class TransactionFilter:
    date_range: DateRange | None
    search: str | None
    account_ids: list[AccountId] | None
    category_ids: list[CategoryId] | None
    category_group_ids: list[CategoryGroupId] | None
    merchant_ids: list[MerchantId] | None
    merchant_names: list[str] | None
    tag_ids: list[TagId] | None
    goal_ids: list[GoalId] | None
    min_amount: MoneyAmount | None
    max_amount: MoneyAmount | None
    amount_operator: Literal["eq", "gt", "gte", "lt", "lte", "between"] | None
    transaction_types: list[Literal["income", "expense", "transfer", "investment"]] | None
    include_pending: bool = True
    include_hidden: bool = False
    hidden_from_reports: bool | None
    is_split: bool | None
    is_recurring: bool | None
    has_notes: bool | None
    has_attachments: bool | None
    needs_review: bool | None
    reviewed: bool | None
    reviewed_by: list[MemberId] | None
    synced_from_institution: bool | None
    imported_from_mint: bool | None

class TransactionSort:
    field: Literal["date", "amount", "merchant", "category", "account", "updated_at"]
    direction: Literal["asc", "desc"] = "desc"

class TransactionCreate:
    date: Date
    account_id: AccountId
    amount: MoneyAmount
    merchant_name: str
    category_id: CategoryId | None
    notes: str | None = None
    tag_ids: list[TagId] | None = None
    update_balance: bool = False

class TransactionPatch:
    date: Date | None
    amount: MoneyAmount | None
    account_id: AccountId | None
    merchant_name: str | None
    merchant_id: MerchantId | None
    category_id: CategoryId | None
    notes: str | None
    tag_ids: list[TagId] | None
    hidden_from_reports: bool | None
    reviewed: bool | None
    needs_review: bool | None
    goal_id: GoalId | None

class TransactionSplit:
    id: TransactionId | None
    parent_transaction_id: TransactionId
    date: Date
    amount: MoneyAmount
    merchant_name: str
    category: CategoryRef | None
    notes: str | None
    tag_ids: list[TagId]

class TransactionSplitInput:
    amount: MoneyAmount
    category_id: CategoryId | None
    merchant_name: str | None
    notes: str | None
    tag_ids: list[TagId] | None

class TransactionAttachment:
    id: AttachmentId
    transaction_id: TransactionId
    filename: str
    content_type: str
    size_bytes: int | None
    url: str | None
    created_at: DateTime | None

class TransactionSummary:
    total_count: int
    income_total: MoneyAmount
    expense_total: MoneyAmount
    transfer_total: MoneyAmount
    net_total: MoneyAmount
```

### Cashflow And Reports Types

```python
CashflowGroupBy = Literal["category_group", "category", "merchant", "account", "tag"]
TimeInterval = Literal["day", "week", "month", "quarter", "year"]

class CashflowFilter:
    date_range: DateRange
    account_ids: list[AccountId] | None
    category_ids: list[CategoryId] | None
    category_group_ids: list[CategoryGroupId] | None
    merchant_ids: list[MerchantId] | None
    tag_ids: list[TagId] | None
    include_hidden: bool = False
    include_transfers: bool = False

class CashflowSummary:
    income: MoneyAmount
    expenses: MoneyAmount
    net_cashflow: MoneyAmount
    savings: MoneyAmount
    savings_rate: Decimal | None
    date_range: DateRange

class CashflowBreakdownRow:
    key: str
    label: str
    group_by: CashflowGroupBy
    income: MoneyAmount
    expenses: MoneyAmount
    net: MoneyAmount
    transaction_count: int
    percent_of_total: Decimal | None

class CashflowTrendPoint:
    period_start: Date
    period_end: Date
    key: str | None
    label: str | None
    income: MoneyAmount
    expenses: MoneyAmount
    net: MoneyAmount

class SavingsRatePoint:
    period_start: Date
    period_end: Date
    savings: MoneyAmount
    income: MoneyAmount
    savings_rate: Decimal | None

class SankeyGraph:
    nodes: list[SankeyNode]
    links: list[SankeyLink]

class SankeyNode:
    id: str
    label: str
    kind: Literal["income", "category_group", "category", "merchant", "expense", "savings"]

class SankeyLink:
    source: str
    target: str
    amount: MoneyAmount
```

```python
ReportKind = Literal["cashflow", "spending", "income"]
ReportMode = Literal["breakdown", "trends"]
ReportChartType = Literal["sankey", "donut", "horizontal_bar", "grouped_bar", "stacked_bar"]
ExportFormat = Literal["csv", "xlsx", "json", "png"]

class ReportRequest:
    kind: ReportKind
    mode: ReportMode
    chart_type: ReportChartType | None
    date_range: DateRange
    interval: TimeInterval | None
    group_by: CashflowGroupBy
    filter: TransactionFilter | CashflowFilter | None

class ReportResult:
    request: ReportRequest
    summary: CashflowSummary | None
    rows: list[ReportRow]
    series: list[ReportSeries] | None
    sankey: SankeyGraph | None

class ReportRow:
    key: str
    label: str
    amount: MoneyAmount
    transaction_count: int
    percent_of_total: Decimal | None

class ReportSeries:
    key: str
    label: str
    points: list[ReportPoint]

class ReportPoint:
    period_start: Date
    period_end: Date
    amount: MoneyAmount

class SavedReport:
    id: ReportId
    name: str
    request: ReportRequest
    created_at: DateTime
    updated_at: DateTime

class SavedReportCreate:
    name: str
    request: ReportRequest

class SavedReportPatch:
    name: str | None
    request: ReportRequest | None

class ReportSelection:
    key: str
    period_start: Date | None
    period_end: Date | None

class ReportExport:
    filename: str
    content_type: str
    bytes: bytes | None
    url: str | None
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
    group: CategoryGroupRef
    planned: MoneyAmount
    actual: MoneyAmount
    remaining: MoneyAmount
    categories: list[BudgetCategoryRow]

class BudgetCategoryRow:
    category: CategoryRef
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
Frequency = Literal["weekly", "biweekly", "monthly", "quarterly", "yearly", "irregular", "unknown"]

class RecurringItem:
    id: RecurringId
    merchant: MerchantRef | None
    merchant_name: str
    account: AccountRef | None
    category: CategoryRef | None
    amount: MoneyAmount | None
    amount_range: AmountRange | None
    frequency: Frequency
    next_expected_date: Date | None
    last_seen_date: Date | None
    status: Literal["active", "ignored", "ended", "unknown"]
    transaction_ids: list[TransactionId]

class AmountRange:
    min_amount: MoneyAmount
    max_amount: MoneyAmount

class RecurringFilter:
    account_ids: list[AccountId] | None
    merchant_ids: list[MerchantId] | None
    category_ids: list[CategoryId] | None
    frequencies: list[Frequency] | None
    status: list[str] | None
    date_range: DateRange | None

class RecurringOccurrence:
    recurring_id: RecurringId
    expected_date: Date
    expected_amount: MoneyAmount | None
    merchant_name: str
    account: AccountRef | None
    category: CategoryRef | None
    matched_transaction_id: TransactionId | None

class RecurringCalendarDay:
    date: Date
    occurrences: list[RecurringOccurrence]

class RecurringCreateFromTransaction:
    frequency: Frequency | None
    next_expected_date: Date | None
    amount: MoneyAmount | None

class RecurringPatch:
    frequency: Frequency | None
    next_expected_date: Date | None
    amount: MoneyAmount | None
    category_id: CategoryId | None
    status: str | None
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
    account: AccountRef
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
    account: AccountRef
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
CategoryKind = Literal["income", "expense", "transfer"]

class CategoryGroup:
    id: CategoryGroupId
    name: str
    kind: CategoryKind
    order: int
    is_system: bool
    is_active: bool
    categories: list[Category]

class Category:
    id: CategoryId
    group_id: CategoryGroupId
    name: str
    emoji: str | None
    kind: CategoryKind
    order: int
    is_system: bool
    is_active: bool
    rollover_enabled: bool | None
    created_at: DateTime | None
    updated_at: DateTime | None

class CategoryFilter:
    group_ids: list[CategoryGroupId] | None
    kinds: list[CategoryKind] | None
    search: str | None
    include_inactive: bool = False

class CategoryTree:
    groups: list[CategoryGroup]

class CategoryGroupCreate:
    name: str
    kind: CategoryKind
    position: int | None

class CategoryGroupPatch:
    name: str | None
    kind: CategoryKind | None

class CategoryCreate:
    group_id: CategoryGroupId
    name: str
    emoji: str | None
    kind: CategoryKind
    position: int | None
    rollover_settings: RolloverSettings | None

class CategoryPatch:
    name: str | None
    emoji: str | None
    group_id: CategoryGroupId | None
    kind: CategoryKind | None
    rollover_settings: RolloverSettings | None
    is_active: bool | None
```

### Merchants Types

```python
class Merchant:
    id: MerchantId
    name: str
    logo_url: str | None
    website_url: str | None
    category: CategoryRef | None
    transaction_count: int | None
    last_transaction_date: Date | None
    created_at: DateTime | None
    updated_at: DateTime | None

class MerchantFilter:
    search: str | None
    category_ids: list[CategoryId] | None
    account_ids: list[AccountId] | None
    has_recurring: bool | None
    date_range: DateRange | None

class MerchantPatch:
    name: str | None
    category_id: CategoryId | None
    logo_url: str | None
    website_url: str | None

class MerchantSummary:
    merchant: Merchant
    total_spend: MoneyAmount
    total_income: MoneyAmount
    transaction_count: int
    average_amount: MoneyAmount | None
    first_transaction_date: Date | None
    last_transaction_date: Date | None
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
    created_by: MemberRef | None
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
    is_archived: bool
    transaction_count: int | None
    created_at: DateTime | None
    updated_at: DateTime | None

class TagCreate:
    name: str
    color: str | None

class TagPatch:
    name: str | None
    color: str | None
    is_archived: bool | None

class TagSummary:
    tag: Tag
    total_spend: MoneyAmount
    total_income: MoneyAmount
    transaction_count: int
```

### Household Types

```python
class Household:
    id: str
    name: str | None
    members: list[HouseholdMember]
    created_at: DateTime | None

class HouseholdMember:
    id: MemberId
    email: str
    display_name: str
    role: HouseholdRole
    status: Literal["active", "invited", "removed"]
    avatar_url: str | None
    joined_at: DateTime | None

HouseholdRole = Literal["manager", "member", "advisor"]

class HouseholdInvite:
    id: InviteId
    email: str
    role: HouseholdRole
    status: Literal["pending", "accepted", "expired", "revoked"]
    invited_at: DateTime
    expires_at: DateTime | None

class UserProfile:
    id: MemberId
    email: str
    display_name: str
    avatar_url: str | None
    timezone: str | None
    notification_preferences: dict[str, object] | None

class UserProfilePatch:
    display_name: str | None
    timezone: str | None
    notification_preferences: dict[str, object] | None

class HouseholdPreferences:
    transaction_review_settings: dict[str, object] | None
    default_currency: str | None
    hide_hidden_transactions_by_default: bool | None
    shared_view_settings: dict[str, object] | None

class HouseholdPreferencesPatch:
    transaction_review_settings: dict[str, object] | None
    hide_hidden_transactions_by_default: bool | None
    shared_view_settings: dict[str, object] | None

class SubscriptionDetails:
    status: Literal["trial", "active", "past_due", "cancelled", "unknown"]
    plan_name: str | None
    renews_at: DateTime | None
    trial_ends_at: DateTime | None
```

### Lightweight Reference Types

Use reference types inside larger models to avoid pulling full object graphs everywhere.

```python
class AccountRef:
    id: AccountId
    display_name: str
    type: str | None
    subtype: str | None

class CategoryRef:
    id: CategoryId
    name: str
    emoji: str | None
    group_id: CategoryGroupId | None
    kind: CategoryKind | None

class CategoryGroupRef:
    id: CategoryGroupId
    name: str
    kind: CategoryKind | None

class TagRef:
    id: TagId
    name: str
    color: str | None

class MerchantRef:
    id: MerchantId | None
    name: str
    logo_url: str | None

class MemberRef:
    id: MemberId
    display_name: str
    email: str | None
```

## Recommended Implementation Order

1. Auth login/session support, MFA challenge handling, logout, current-user lookup, and password flows.
2. Accounts read functions, manual accounts, balances, and net worth history.
3. Categories, Tags, and Merchants read functions.
4. Transactions list/detail/update/split/delete with the full `TransactionFilter`.
5. Cashflow summary and breakdown.
6. Budget read and planned amount updates.
7. Recurring read functions.
8. Rules CRUD, preview, order, and apply-to-existing.
9. Goals CRUD and transaction links.
10. Investments holdings, allocation, and performance.
11. Reports and saved reports.
12. Household members, invites, preferences, and subscription details.

## Source Notes

This plan is based on Monarch's public help documentation for current web-app functionality and on community API surfaces used as hints for feasible operations:

- Monarch help: [Default Categories](https://help.monarch.com/hc/en-us/articles/360048883851-Default-Categories), [Budget](https://help.monarchmoney.com/hc/en-us/articles/360048883631-Budget), [Using Goals](https://help.monarchmoney.com/hc/en-us/articles/15000751305108-Using-Goals), [Using Reports](https://help.monarch.com/hc/en-us/articles/21846787088916-Using-Reports), [Cash Flow](https://help.monarchmoney.com/hc/en-us/articles/20504904768020-Cash-Flow), [Creating Transaction Rules](https://help.monarch.com/hc/en-us/articles/360048393372-Creating-Transaction-Rules), [Hiding or Unhiding Transactions](https://help.monarch.com/hc/en-us/articles/4405041904916-Hiding-or-Unhiding-Transactions), [Investments in Monarch](https://help.monarch.com/hc/en-us/articles/41855507661076-Investments-in-Monarch), [Manual Investment Holdings](https://help.monarchmoney.com/hc/en-us/articles/10032888165140-Manual-Investment-Holdings), and [Add Members to an Existing Account](https://help.monarchmoney.com/hc/en-us/articles/360048393452-Add-Members-to-an-Existing-Account).
- Community clients: [hammem/monarchmoney](https://github.com/hammem/monarchmoney) and [pbassham/monarch-money-api](https://github.com/pbassham/monarch-money-api).

Because Monarch does not publish a stable public API contract, every implementation should expect GraphQL operation names, fields, and auth behavior to change.
