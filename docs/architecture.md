# Banking Application - Data Model & Architecture

## Overview

This document describes the core data model for a production-ready banking application. The architecture is designed to handle real-world loads with strong consistency guarantees, audit trails, and immutable transaction history.

## Core Principles

### 1. Source of Truth
- **LedgerEntry** is the single source of truth for all financial operations
- Account balances are **derived state** calculated from ledger entries
- All money movements must be recorded as ledger entries

### 2. Immutability
- **LedgerEntry** records are immutable once created
- **Transaction** records are immutable once committed
- **AuditLog** entries are append-only

### 3. Double-Entry Bookkeeping
- Every transaction creates ≥ 2 ledger entries (debit and credit)
- Sum of all debits = Sum of all credits (system invariant)
- Balance is never stored directly, always calculated

## Entity-Relationship Model

### 1. User
Represents a customer of the bank.

**Attributes:**
- `id` (UUID, PK) - Unique identifier
- `email` (String, Unique, Indexed) - User email
- `full_name` (String) - User's full name
- `password_hash` (String) - Hashed password
- `created_at` (Timestamp) - Account creation time
- `updated_at` (Timestamp) - Last update time
- `is_active` (Boolean) - Account status

**Relationships:**
- One User → Many BankAccounts
- One User → Many AuditLogs (as actor)

**Invariants:**
- Email must be unique and valid
- Password must be hashed (never store plaintext)
- Cannot delete user with active accounts

---

### 2. BankAccount
Represents a bank account owned by a user.

**Attributes:**
- `id` (UUID, PK) - Unique identifier
- `user_id` (UUID, FK → User) - Account owner
- `account_number` (String, Unique, Indexed) - Human-readable account number
- `account_type` (Enum) - CHECKING, SAVINGS, BUSINESS
- `currency` (String) - ISO 4217 code (USD, EUR, etc.)
- `status` (Enum) - ACTIVE, FROZEN, CLOSED
- `created_at` (Timestamp) - Account opening time
- `updated_at` (Timestamp) - Last update time

**Derived State (NOT stored):**
- `balance` - Calculated from LedgerEntry records

**Relationships:**
- Many BankAccounts → One User
- One BankAccount → Many LedgerEntries
- One BankAccount → Many Transactions (as source or destination)

**Invariants:**
- Account number must be unique
- Cannot delete account with non-zero balance
- Cannot delete account with pending transactions
- Balance calculation: `SUM(ledger_entries.amount WHERE account_id = this.id)`

---

### 3. Transaction
Represents a financial operation between accounts or external systems.

**Attributes:**
- `id` (UUID, PK) - Unique identifier
- `transaction_type` (Enum) - TRANSFER, DEPOSIT, WITHDRAWAL, FEE
- `source_account_id` (UUID, FK → BankAccount, Nullable) - Source account
- `destination_account_id` (UUID, FK → BankAccount, Nullable) - Destination account
- `amount` (Decimal) - Transaction amount (positive)
- `currency` (String) - ISO 4217 code
- `status` (Enum) - PENDING, COMPLETED, FAILED, REVERSED
- `description` (String) - Transaction description
- `idempotency_key` (String, Unique, Indexed) - For duplicate prevention
- `created_at` (Timestamp) - Transaction initiation time
- `completed_at` (Timestamp, Nullable) - Transaction completion time
- `metadata` (JSONB) - Additional transaction data

**Relationships:**
- One Transaction → Many LedgerEntries (≥ 2)
- Many Transactions → One BankAccount (as source)
- Many Transactions → One BankAccount (as destination)

**Invariants:**
- Amount must be positive
- Status transitions: PENDING → COMPLETED or FAILED
- Once COMPLETED, transaction is immutable
- Must create exactly 2 ledger entries for transfers (debit + credit)
- Must create ≥ 1 ledger entry for deposits/withdrawals
- `idempotency_key` prevents duplicate transactions

---

### 4. LedgerEntry
**SOURCE OF TRUTH** - Immutable record of all money movements.

**Attributes:**
- `id` (UUID, PK) - Unique identifier
- `transaction_id` (UUID, FK → Transaction) - Parent transaction
- `account_id` (UUID, FK → BankAccount) - Affected account
- `amount` (Decimal) - Signed amount (positive = credit, negative = debit)
- `balance_after` (Decimal) - Account balance after this entry (snapshot)
- `entry_type` (Enum) - DEBIT, CREDIT
- `created_at` (Timestamp) - Entry creation time (immutable)
- `sequence_number` (BigInt) - Monotonic sequence per account

**Relationships:**
- Many LedgerEntries → One Transaction
- Many LedgerEntries → One BankAccount

**Invariants:**
- Entries are **immutable** - never updated or deleted
- Entries are **append-only**
- `sequence_number` is monotonically increasing per account
- For any transaction: `SUM(ledger_entries.amount) = 0` (double-entry)
- `balance_after` is calculated at insertion time for verification
- Entries must be created within a database transaction

**Balance Calculation:**
```sql
-- Current balance for an account
SELECT balance_after 
FROM ledger_entries 
WHERE account_id = ? 
ORDER BY sequence_number DESC 
LIMIT 1;

-- Or calculate from scratch
SELECT SUM(amount) 
FROM ledger_entries 
WHERE account_id = ?;
```

---

### 5. AuditLog
Append-only log of all system actions for compliance and debugging.

**Attributes:**
- `id` (UUID, PK) - Unique identifier
- `actor_id` (UUID, FK → User, Nullable) - Who performed the action
- `action_type` (Enum) - LOGIN, TRANSACTION_CREATE, ACCOUNT_UPDATE, etc.
- `entity_type` (String) - Type of affected entity
- `entity_id` (UUID) - ID of affected entity
- `changes` (JSONB) - Before/after state
- `ip_address` (String) - Request IP
- `user_agent` (String) - Request user agent
- `created_at` (Timestamp) - Log entry time
- `metadata` (JSONB) - Additional context

**Relationships:**
- Many AuditLogs → One User (as actor)

**Invariants:**
- Entries are **immutable** and **append-only**
- Never deleted (retention policy: archive after N years)
- Must log all state-changing operations

---

## System Invariants

### Financial Invariants
1. **Zero-Sum**: For any transaction, `SUM(ledger_entries.amount) = 0`
2. **Balance Consistency**: Account balance = `SUM(ledger_entries.amount)` for that account
3. **No Negative Balances**: Account balance ≥ 0 (enforced at transaction level)
4. **Immutable History**: LedgerEntry and completed Transactions cannot be modified

### Data Integrity Invariants
1. **No Orphans**: Every LedgerEntry must reference a valid Transaction and BankAccount
2. **No Cycles**: Dependency graph is acyclic (User → BankAccount → LedgerEntry ← Transaction)
3. **Idempotency**: Duplicate transactions prevented via `idempotency_key`
4. **Audit Trail**: All state changes must create AuditLog entries

### Concurrency Invariants
1. **Atomic Transactions**: All ledger entries for a transaction created atomically
2. **Sequential Consistency**: `sequence_number` prevents race conditions
3. **Optimistic Locking**: Use `updated_at` for version control on mutable entities

---

## Dependency Graph (Acyclic)

```
User
  ↓
BankAccount
  ↓
LedgerEntry ← Transaction
  ↓
AuditLog
```

**No circular dependencies:**
- User depends on nothing
- BankAccount depends on User
- Transaction depends on BankAccount (optional references)
- LedgerEntry depends on Transaction and BankAccount
- AuditLog depends on User (optional) and tracks all entities

---

## Transaction Flow Example

### Transfer: Account A → Account B ($100)

1. **Create Transaction**
   ```
   Transaction {
     id: tx_123,
     type: TRANSFER,
     source_account_id: account_A,
     destination_account_id: account_B,
     amount: 100.00,
     status: PENDING
   }
   ```

2. **Create Ledger Entries** (atomic)
   ```
   LedgerEntry {
     id: le_1,
     transaction_id: tx_123,
     account_id: account_A,
     amount: -100.00,  // DEBIT
     entry_type: DEBIT,
     balance_after: 900.00
   }
   
   LedgerEntry {
     id: le_2,
     transaction_id: tx_123,
     account_id: account_B,
     amount: +100.00,  // CREDIT
     entry_type: CREDIT,
     balance_after: 1100.00
   }
   ```

3. **Update Transaction Status**
   ```
   Transaction.status = COMPLETED
   Transaction.completed_at = NOW()
   ```

4. **Create Audit Logs**
   ```
   AuditLog { action: TRANSACTION_CREATE, entity_id: tx_123, ... }
   AuditLog { action: ACCOUNT_DEBIT, entity_id: account_A, ... }
   AuditLog { action: ACCOUNT_CREDIT, entity_id: account_B, ... }
   ```

**Invariant Check:**
- Sum of ledger entries: -100 + 100 = 0 ✓
- Account A balance: previous - 100 ✓
- Account B balance: previous + 100 ✓

---

## Why This Design?

### Scalability
- Ledger entries are append-only (no updates = better performance)
- Balance calculation can be cached/materialized
- Horizontal partitioning by account_id

### Reliability
- Immutable ledger = audit trail by design
- Double-entry bookkeeping catches errors
- Idempotency prevents duplicate transactions

### Compliance
- Complete audit trail in AuditLog
- Immutable transaction history
- Can reconstruct any account state at any point in time

### Maintainability
- Clear separation of concerns
- No circular dependencies
- Single source of truth (LedgerEntry)

---

## 5-Minute Explanation

**For any backend developer:**

1. **Users** own **BankAccounts**
2. **Transactions** move money between accounts
3. **LedgerEntry** is the source of truth - every transaction creates ≥2 entries (debit + credit)
4. **Balance is calculated**, not stored - sum all ledger entries for an account
5. **AuditLog** tracks everything for compliance
6. **Immutability**: Ledger entries and completed transactions never change
7. **Invariant**: Sum of all ledger entries for a transaction = 0 (double-entry bookkeeping)

**Dependencies flow one way**: User → BankAccount → LedgerEntry ← Transaction → AuditLog

**No cycles. No magic. Just solid accounting principles.**

---

## Next Steps

1. Implement database schema (PostgreSQL recommended)
2. Create database migrations
3. Implement repository layer with invariant checks
4. Add transaction service with ACID guarantees
5. Implement balance calculation with caching
6. Add comprehensive tests for all invariants
