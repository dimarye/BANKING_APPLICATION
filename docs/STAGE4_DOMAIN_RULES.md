# Stage 4 — Domain Rules: BankAccount & Locking

## Account Types

```python
ACCOUNT_TYPE_RETAIL = "RETAIL"
ACCOUNT_TYPE_BUSINESS = "BUSINESS"
```

## Account Status

```python
STATUS_ACTIVE = "ACTIVE"
STATUS_FROZEN = "FROZEN"
STATUS_CLOSED = "CLOSED"
```

## Domain Invariants

### Balance Calculation
- **Balance is NEVER stored** in BankAccount model
- Balance = `SUM(debit_entries.amount) - SUM(credit_entries.amount)` from Ledger
- Balance is calculated via `ledger.get_account_balance(account, currency)`

### Balance Constraints by Account Type

#### RETAIL Accounts
- `balance >= 0` **always**
- No overdraft allowed
- Any operation that would result in negative balance **must be rejected**

#### BUSINESS Accounts
- `balance >= -overdraft_limit`
- `overdraft_limit` is a positive Decimal field on BankAccount
- Default `overdraft_limit = 0` (no overdraft unless explicitly set)

### Transaction Rules

1. **Atomicity**: Every account operation must be wrapped in `transaction.atomic()`
2. **Locking**: Any balance read before debit must use `select_for_update()`
3. **Lock Order**: When locking multiple accounts, always lock by `id ASC` to prevent deadlocks
4. **Status Check**: Operations only allowed on `ACTIVE` accounts
5. **Currency Match**: All accounts in a transaction must have matching currency

## Locking Strategy

### Standard Pattern for All Operations

```python
with transaction.atomic():
    # 1. Lock account(s) in deterministic order
    account = BankAccount.objects.select_for_update().get(id=account_id)
    
    # 2. Read balance AFTER lock
    balance = get_account_balance(account, account.currency)
    
    # 3. Check business invariants
    if not is_operation_allowed(account, balance, amount):
        raise BusinessRuleViolation
    
    # 4. Write to Ledger
    LedgerService.create_entry(...)
    
    # 5. Commit (automatic at end of with block)
```

### Transfer Pattern (Two Accounts)

```python
with transaction.atomic():
    # Lock both accounts in ID order to prevent deadlock
    if from_account.id < to_account.id:
        from_acc = BankAccount.objects.select_for_update().get(id=from_account.id)
        to_acc = BankAccount.objects.select_for_update().get(id=to_account.id)
    else:
        to_acc = BankAccount.objects.select_for_update().get(id=to_account.id)
        from_acc = BankAccount.objects.select_for_update().get(id=from_account.id)
    
    # Read balances after lock
    from_balance = get_account_balance(from_acc, from_acc.currency)
    
    # Check invariants
    # ... business logic
    
    # Write to Ledger
    LedgerService.create_entry(
        debit_account=internal_account_for(from_acc),
        credit_account=internal_account_for(to_acc),
        amount=amount,
        currency=currency
    )
```

## Forbidden Patterns

### ❌ Reading balance without lock
```python
# WRONG - race condition
balance = get_account_balance(account, currency)
if balance >= amount:
    # Another thread can withdraw here!
    withdraw(account, amount)
```

### ❌ Caching balance
```python
# WRONG - stale data
account.cached_balance = get_account_balance(...)
```

### ❌ Multiple transactions for one operation
```python
# WRONG - not atomic
with transaction.atomic():
    check_balance(account)

with transaction.atomic():  # Another thread can interfere here!
    withdraw(account, amount)
```

### ❌ Writing to Ledger outside AccountService
```python
# WRONG - bypasses business rules
LedgerEntry.objects.create(...)  # This is blocked anyway
LedgerService.create_entry(...)  # Must go through AccountService
```

## Enforcement

- **Code Level**: AccountService is the ONLY way to perform account operations
- **Test Level**: Concurrency tests must verify no race conditions
- **Review Level**: Any PR touching accounts must demonstrate proper locking

## Success Criteria

- ✅ No balance field in BankAccount model
- ✅ All operations use `select_for_update()`
- ✅ Lock order is deterministic (by ID)
- ✅ RETAIL accounts cannot go negative
- ✅ BUSINESS accounts respect overdraft_limit
- ✅ Concurrent operations are serialized correctly
- ✅ Tests prove no race conditions exist
