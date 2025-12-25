# Banking System Invariants

## Critical Business Rules

This document defines the invariants that MUST be maintained at all times in the banking system. These are enforced at the application and database levels.

## Financial Invariants

### 1. Double-Entry Bookkeeping

**Rule**: For every transaction, the sum of all ledger entries must equal zero.

```text
∀ transaction_id: SUM(ledger_entries.amount WHERE transaction_id = t) = 0
```

**Enforcement**:

- Application: Validate before committing transaction
- Database: Check constraint or trigger
- Test: Every transaction test must verify this

**Example**:

```text
Transfer $100 from Account A to Account B:
- LedgerEntry 1: amount = -100 (debit from A)
- LedgerEntry 2: amount = +100 (credit to B)
- Sum: -100 + 100 = 0 ✓
```

### 2. Balance Consistency

**Rule**: Account balance must always equal the sum of all its ledger entries.

```text
∀ account_id: balance = SUM(ledger_entries.amount WHERE account_id = a)
```

**Enforcement**:

- Balance is NEVER stored directly in BankAccount table
- Balance is always calculated from LedgerEntry
- Can be cached with invalidation strategy

**Verification**:

```sql
-- This query should always return 0 rows
SELECT account_id,
       cached_balance,
       (SELECT SUM(amount) FROM ledger_entries WHERE account_id = ba.id) as actual_balance
FROM bank_accounts ba
WHERE cached_balance != (SELECT SUM(amount) FROM ledger_entries WHERE account_id = ba.id);
```

### 3. Non-Negative Balance

**Rule**: Account balance cannot go below zero (overdraft protection).

```text
∀ account_id: SUM(ledger_entries.amount WHERE account_id = a) ≥ 0
```

**Enforcement**:

- Check before creating debit ledger entry
- Use database constraint or trigger
- Reject transaction if would cause negative balance

**Exception**: Business accounts may have overdraft limits (separate feature).

### 4. Positive Transaction Amounts

**Rule**: Transaction amounts must be positive.

```text
∀ transaction: transaction.amount > 0
```

**Rationale**: Sign is determined by entry_type (DEBIT/CREDIT), not by amount.

### 5. Minimum Ledger Entries per Transaction

**Rule**: Every transaction must create at least 2 ledger entries.

```text
∀ transaction: COUNT(ledger_entries WHERE transaction_id = t) ≥ 2
```

**Breakdown by type**:

- TRANSFER: exactly 2 entries (source debit + destination credit)
- DEPOSIT: 2 entries (external debit + account credit)
- WITHDRAWAL: 2 entries (account debit + external credit)
- FEE: 2 entries (account debit + revenue credit)

## Data Integrity Invariants

### 6. Immutability of Ledger Entries

**Rule**: LedgerEntry records cannot be modified or deleted once created.

**Enforcement**:

- Database: Revoke UPDATE and DELETE permissions
- Application: No update/delete methods in repository
- Audit: Log any attempted modifications

**Correction**: To fix errors, create reversing entries, never modify originals.

### 7. Immutability of Completed Transactions

**Rule**: Transactions with status=COMPLETED cannot be modified.

**Enforcement**:

- Database: Trigger to prevent updates when status=COMPLETED
- Application: Validate status before any update
- Audit: Log any attempted modifications

**Allowed transitions**:

- PENDING → COMPLETED ✓
- PENDING → FAILED ✓
- COMPLETED → REVERSED ✓ (creates new reversing transaction)
- COMPLETED → PENDING ✗
- COMPLETED → FAILED ✗

### 8. Referential Integrity

**Rule**: No orphaned records.

```text
∀ ledger_entry:
  - transaction_id references valid Transaction
  - account_id references valid BankAccount

∀ bank_account:
  - user_id references valid User

∀ transaction:
  - source_account_id references valid BankAccount (if not null)
  - destination_account_id references valid BankAccount (if not null)
```

**Enforcement**:

- Database: Foreign key constraints with appropriate CASCADE rules
- Application: Validate references before creation

### 9. Uniqueness Constraints

**Rule**: Certain fields must be globally unique.

```text
- User.email: UNIQUE
- BankAccount.account_number: UNIQUE
- Transaction.idempotency_key: UNIQUE
- LedgerEntry.sequence_number: UNIQUE per account_id
```

**Enforcement**:

- Database: UNIQUE constraints and indexes
- Application: Check before insert (with retry logic for conflicts)

### 10. No Circular Dependencies

**Rule**: Entity dependency graph must be acyclic.

```text
User → BankAccount → LedgerEntry ← Transaction
                  ↓
              AuditLog
```

**Verification**: Topological sort of dependencies must succeed.

## Concurrency Invariants

### 11. Atomic Transaction Creation

**Rule**: All ledger entries for a transaction must be created atomically.

**Enforcement**:

- Database: Use database transactions (BEGIN/COMMIT)
- Application: All ledger entries created in single transaction
- Rollback: If any entry fails, rollback entire transaction

**Example**:

```python
with db.transaction():
    transaction = create_transaction(...)
    ledger_entry_1 = create_ledger_entry(...)
    ledger_entry_2 = create_ledger_entry(...)
    transaction.status = COMPLETED
    # All or nothing
```

### 12. Sequential Consistency

**Rule**: Ledger entries for an account must have monotonically increasing sequence numbers.

```text
∀ account_id: ledger_entries.sequence_number is strictly increasing
```

**Enforcement**:

- Database: Use sequence or auto-increment per account
- Application: Lock account during ledger entry creation
- Prevents: Race conditions in balance calculation

### 13. Idempotency

**Rule**: Duplicate transaction requests must not create duplicate transactions.

```text
∀ idempotency_key: COUNT(transactions WHERE idempotency_key = k) ≤ 1
```

**Enforcement**:

- Database: UNIQUE constraint on idempotency_key
- Application: Check for existing transaction before creation
- Return: Existing transaction if idempotency_key matches

### 14. Optimistic Locking

**Rule**: Concurrent updates to mutable entities must be detected.

**Enforcement**:

- Add `version` or `updated_at` column
- Check version before update
- Reject update if version mismatch

**Example**:

```sql
UPDATE bank_accounts
SET status = 'FROZEN', updated_at = NOW()
WHERE id = ? AND updated_at = ?  -- Check version
```

## Audit Invariants

### 15. Complete Audit Trail

**Rule**: All state-changing operations must create audit log entries.

**Required events**:

- User: CREATE, UPDATE, DELETE, LOGIN, LOGOUT
- BankAccount: CREATE, UPDATE, FREEZE, CLOSE
- Transaction: CREATE, COMPLETE, FAIL, REVERSE
- LedgerEntry: CREATE (never UPDATE/DELETE)

**Enforcement**:

- Application: Middleware/decorator to auto-log
- Database: Triggers as backup
- Monitoring: Alert on missing audit logs

### 16. Immutable Audit Logs

**Rule**: AuditLog entries cannot be modified or deleted.

**Enforcement**:

- Database: Revoke UPDATE and DELETE permissions
- Application: No update/delete methods
- Retention: Archive after N years, never delete

## Validation Invariants

### 17. Currency Consistency

**Rule**: All amounts in a transaction must use the same currency.

```text
∀ transaction:
  transaction.currency = ledger_entries[*].currency
```

**Enforcement**:

- Application: Validate before creating ledger entries
- Database: Check constraint (if storing currency per entry)

### 18. Account Status Checks

**Rule**: Transactions can only involve ACTIVE accounts.

```text
∀ transaction:
  - source_account.status = ACTIVE (if not null)
  - destination_account.status = ACTIVE (if not null)
```

**Enforcement**:

- Application: Check account status before transaction
- Reject: Transactions involving FROZEN or CLOSED accounts

### 19. Valid Enum Values

**Rule**: Enum fields must contain only valid values.

**Enforcement**:

- Database: ENUM type or CHECK constraint
- Application: Use type-safe enums
- Validation: Reject invalid values at API boundary

## Testing Invariants

Every invariant must have:

1. **Unit test**: Verify enforcement logic
2. **Integration test**: Verify database constraints
3. **Property test**: Generate random scenarios
4. **Load test**: Verify under concurrency

## Monitoring Invariants

Set up alerts for:

- Invariant violations detected
- Attempted modifications to immutable data
- Balance calculation mismatches
- Missing audit log entries
- Failed transaction rollbacks

## Recovery Procedures

If an invariant is violated:

1. **Immediate**: Stop affected operations
2. **Investigate**: Identify root cause
3. **Fix**: Correct data (with audit trail)
4. **Prevent**: Add safeguards to prevent recurrence
5. **Document**: Update runbook

## Summary

**Critical invariants (must never be violated)**:

- Double-entry bookkeeping (sum = 0)
- Balance consistency
- Immutability of ledger entries
- Atomic transaction creation

**Important invariants (should be enforced)**:

- Non-negative balance
- Referential integrity
- Idempotency
- Complete audit trail

**Nice-to-have invariants (can be relaxed)**:

- Currency consistency (if supporting multi-currency)
- Account status checks (if supporting overdrafts)
