# Entity-Relationship Diagram

## Banking Application Data Model

```mermaid
erDiagram
    User ||--o{ BankAccount : "owns"
    User ||--o{ AuditLog : "performs"
    BankAccount ||--o{ LedgerEntry : "has"
    BankAccount ||--o{ Transaction : "source"
    BankAccount ||--o{ Transaction : "destination"
    Transaction ||--|{ LedgerEntry : "creates"
    
    User {
        uuid id PK
        string email UK "Unique, Indexed"
        string full_name
        string password_hash
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }
    
    BankAccount {
        uuid id PK
        uuid user_id FK
        string account_number UK "Unique, Indexed"
        enum account_type "CHECKING, SAVINGS, BUSINESS"
        string currency "ISO 4217"
        enum status "ACTIVE, FROZEN, CLOSED"
        timestamp created_at
        timestamp updated_at
    }
    
    Transaction {
        uuid id PK
        enum transaction_type "TRANSFER, DEPOSIT, WITHDRAWAL, FEE"
        uuid source_account_id FK "Nullable"
        uuid destination_account_id FK "Nullable"
        decimal amount "Positive"
        string currency "ISO 4217"
        enum status "PENDING, COMPLETED, FAILED, REVERSED"
        string description
        string idempotency_key UK "Unique, Indexed"
        timestamp created_at
        timestamp completed_at "Nullable"
        jsonb metadata
    }
    
    LedgerEntry {
        uuid id PK
        uuid transaction_id FK
        uuid account_id FK
        decimal amount "Signed: +credit, -debit"
        decimal balance_after "Snapshot"
        enum entry_type "DEBIT, CREDIT"
        timestamp created_at "Immutable"
        bigint sequence_number "Monotonic per account"
    }
    
    AuditLog {
        uuid id PK
        uuid actor_id FK "Nullable"
        enum action_type "LOGIN, TRANSACTION_CREATE, etc"
        string entity_type
        uuid entity_id
        jsonb changes "Before/after state"
        string ip_address
        string user_agent
        timestamp created_at
        jsonb metadata
    }
```

## Visual Representation (Alternative)

```
┌─────────────┐
│    User     │
│  (Mutable)  │
└──────┬──────┘
       │ 1:N
       ↓
┌─────────────────┐
│  BankAccount    │
│   (Mutable)     │
│                 │
│ balance: DERIVED│ ← Calculated from LedgerEntry
└────┬────────┬───┘
     │        │
     │ 1:N    │ 1:N
     ↓        ↓
┌────────────────┐      ┌──────────────┐
│  Transaction   │ 1:N  │ LedgerEntry  │
│  (Immutable*)  │─────→│ (IMMUTABLE)  │
│                │      │              │
│ *once COMPLETED│      │ SOURCE OF    │
└────────────────┘      │   TRUTH      │
                        └──────────────┘
                               ↓
                        ┌──────────────┐
                        │  AuditLog    │
                        │ (IMMUTABLE)  │
                        │ Append-only  │
                        └──────────────┘
```

## Key Relationships

### 1. User → BankAccount (1:N)
- One user can own multiple bank accounts
- Cascade: Prevent deletion if accounts exist

### 2. BankAccount → LedgerEntry (1:N)
- One account has many ledger entries
- **LedgerEntry is the source of truth for balance**
- Cascade: Prevent deletion (ledger is immutable)

### 3. Transaction → LedgerEntry (1:N, minimum 2)
- Every transaction creates ≥ 2 ledger entries
- For transfers: exactly 2 entries (debit + credit)
- For deposits/withdrawals: ≥ 1 entry
- **Invariant: SUM(ledger_entries.amount) = 0 for each transaction**

### 4. BankAccount → Transaction (N:M via source/destination)
- Account can be source or destination of transactions
- Both fields are nullable (for external deposits/withdrawals)

### 5. User → AuditLog (1:N)
- Tracks all user actions
- Actor can be null for system actions

## Data Flow

```
User Action
    ↓
Create Transaction (PENDING)
    ↓
Validate Business Rules
    ↓
Create LedgerEntries (Atomic)
    ├→ Debit Entry (source account)
    └→ Credit Entry (destination account)
    ↓
Update Transaction (COMPLETED)
    ↓
Create AuditLog Entries
    ↓
Return Success
```

## Dependency Graph (Acyclic)

```
Level 0: User (no dependencies)
         ↓
Level 1: BankAccount (depends on User)
         ↓
Level 2: Transaction (depends on BankAccount - optional)
         ↓
Level 3: LedgerEntry (depends on Transaction + BankAccount)
         ↓
Level 4: AuditLog (depends on User - optional, tracks all entities)
```

**No circular dependencies** - the graph flows in one direction.

## Immutability Markers

- 🔒 **Immutable**: LedgerEntry, AuditLog
- 🔐 **Conditionally Immutable**: Transaction (immutable once COMPLETED)
- 📝 **Mutable**: User, BankAccount

## Source of Truth

```
┌─────────────────────────────────────────┐
│         LedgerEntry Table               │
│                                         │
│  All financial operations recorded here │
│  Balance = SUM(amount) for account_id   │
│  Immutable, append-only                 │
│  Double-entry bookkeeping enforced      │
└─────────────────────────────────────────┘
              ↓
        Single Source
           of Truth
```
