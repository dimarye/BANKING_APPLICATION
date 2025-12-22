# Banking Application - Stage 1: Data Model & Architecture

## 📋 Overview

This directory contains the complete data model and architecture documentation for a production-ready banking application. The design is based on proven accounting principles and can handle real-world loads.

## 📚 Documentation Files

### 1. [architecture.md](./architecture.md)
**Complete data model specification** including:
- 5 core entities (User, BankAccount, Transaction, LedgerEntry, AuditLog)
- Entity attributes and relationships
- Source of truth definition (LedgerEntry)
- Immutability rules
- Derived state (balance calculation)
- Transaction flow examples
- 5-minute explanation for developers

### 2. [er-diagram.md](./er-diagram.md)
**Visual representations** including:
- Mermaid ER diagram
- ASCII art diagram
- Relationship cardinalities
- Data flow visualization
- Dependency graph
- Immutability markers

### 3. [INVARIANTS.md](./INVARIANTS.md)
**System invariants and business rules** including:
- Financial invariants (double-entry bookkeeping, balance consistency)
- Data integrity invariants (immutability, referential integrity)
- Concurrency invariants (atomicity, idempotency)
- Audit invariants (complete trail, immutable logs)
- Validation rules
- Testing requirements
- Monitoring guidelines

## 🎯 Core Principles

### Source of Truth
**LedgerEntry** is the single source of truth for all financial data. Account balances are never stored directly but always calculated from ledger entries.

### Immutability
- ✅ **LedgerEntry**: Immutable (append-only)
- ✅ **Transaction**: Immutable once COMPLETED
- ✅ **AuditLog**: Immutable (append-only)
- ⚠️ **BankAccount**: Mutable (status, metadata)
- ⚠️ **User**: Mutable (profile data)

### Double-Entry Bookkeeping
Every transaction creates ≥ 2 ledger entries where:
```
SUM(ledger_entries.amount) = 0
```

## 🏗️ Entity Summary

| Entity | Purpose | Mutability | Key Constraint |
|--------|---------|------------|----------------|
| **User** | Customer identity | Mutable | Unique email |
| **BankAccount** | User's account | Mutable | Unique account_number |
| **Transaction** | Financial operation | Immutable* | Unique idempotency_key |
| **LedgerEntry** | Source of truth | **Immutable** | Sum per transaction = 0 |
| **AuditLog** | Compliance trail | **Immutable** | Append-only |

*Immutable once status = COMPLETED

## 🔄 Dependency Graph (Acyclic)

```
User (Level 0)
  ↓
BankAccount (Level 1)
  ↓
Transaction (Level 2) ──→ LedgerEntry (Level 3)
  ↓                              ↓
AuditLog (Level 4) ←─────────────┘
```

**No circular dependencies** ✅

## 💡 5-Minute Explanation

For any backend developer:

1. **Users** own **BankAccounts**
2. **Transactions** represent money movements
3. **LedgerEntry** is the source of truth - every transaction creates ≥2 entries (debit + credit)
4. **Balance is calculated**, not stored - sum all ledger entries for an account
5. **AuditLog** tracks everything for compliance
6. **Immutability**: Ledger entries and completed transactions never change
7. **Invariant**: Sum of all ledger entries for a transaction = 0 (double-entry bookkeeping)

## 📊 Key Invariants

### Critical (Must Never Violate)
- ✅ Double-entry bookkeeping: `SUM(ledger_entries.amount) = 0` per transaction
- ✅ Balance consistency: `balance = SUM(ledger_entries.amount)` per account
- ✅ Immutability of ledger entries
- ✅ Atomic transaction creation

### Important (Should Enforce)
- ✅ Non-negative balance (overdraft protection)
- ✅ Referential integrity (no orphans)
- ✅ Idempotency (duplicate prevention)
- ✅ Complete audit trail

## 🔍 Example: Transfer $100

```
1. Create Transaction (PENDING)
   - source: Account A
   - destination: Account B
   - amount: 100.00

2. Create Ledger Entries (atomic)
   - Entry 1: account_id=A, amount=-100.00 (DEBIT)
   - Entry 2: account_id=B, amount=+100.00 (CREDIT)
   - Invariant check: -100 + 100 = 0 ✓

3. Update Transaction (COMPLETED)

4. Create Audit Logs
```

## ✅ Completion Criteria

### Done If:
- [x] Can explain model to any backend developer in 5 minutes
- [x] No circular dependencies in entity graph
- [x] Source of truth clearly defined (LedgerEntry)
- [x] Immutable entities identified
- [x] Derived state documented (balance)
- [x] All invariants documented
- [x] ER diagram created
- [x] Architecture documentation complete

## 🚀 Next Steps

1. **Database Schema** - Implement PostgreSQL schema with constraints
2. **Migrations** - Create database migration scripts
3. **Repository Layer** - Implement data access with invariant checks
4. **Transaction Service** - Build service layer with ACID guarantees
5. **Balance Calculation** - Implement with caching strategy
6. **Testing** - Comprehensive tests for all invariants

## 📖 Reading Order

For new developers joining the project:

1. Start with this README (you are here)
2. Read [architecture.md](./architecture.md) - understand entities and relationships
3. Review [er-diagram.md](./er-diagram.md) - visualize the model
4. Study [INVARIANTS.md](./INVARIANTS.md) - learn the rules that must never break

## 🎓 Key Concepts

### Why LedgerEntry is Source of Truth?
- Immutable = reliable audit trail
- Append-only = high performance
- Double-entry = self-validating
- Historical = can reconstruct any state

### Why Balance is Derived?
- Prevents inconsistencies
- Simplifies concurrency
- Enables point-in-time queries
- Matches accounting principles

### Why Idempotency Keys?
- Prevents duplicate transactions
- Enables safe retries
- Critical for distributed systems
- Industry best practice

## 🛡️ Design Benefits

### Scalability
- Append-only ledger (no updates)
- Horizontal partitioning by account_id
- Balance caching possible

### Reliability
- Immutable history
- Self-validating (double-entry)
- Complete audit trail

### Compliance
- Full transaction history
- Tamper-evident design
- Point-in-time reconstruction

### Maintainability
- Clear separation of concerns
- No circular dependencies
- Single source of truth

## 📝 Notes

- This is a **production-ready** design used by fintech companies
- Based on **double-entry bookkeeping** (500+ years old, battle-tested)
- Prioritizes **correctness over convenience**
- Designed for **auditability and compliance**

---

**Stage 1 Complete** ✅

Ready for implementation in Stage 2.
