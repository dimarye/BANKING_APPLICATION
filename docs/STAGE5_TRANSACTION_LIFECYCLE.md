# Stage 5 — Transaction Lifecycle (Pre-Implementation)

## 1. Status Model

```text
CREATED  →  PENDING  →  COMPLETED
                  \→  FAILED
```

| Status     | Description                                       | Terminal |
|------------|---------------------------------------------------|----------|
| CREATED    | Transaction record created, not yet processed     | No       |
| PENDING    | Business logic executing, ledger untouched        | No       |
| COMPLETED  | Ledger committed successfully, funds transferred  | Yes      |
| FAILED     | Transaction aborted with error, no ledger effect  | Yes      |

### Rules
- `COMPLETED` и `FAILED` — **terminal**: любая попытка изменить статус → ошибка.
- Ledger записи разрешены **только** при переходе `PENDING → COMPLETED`.
- Любой выход из `PENDING`, кроме `COMPLETED`/`FAILED`, запрещён.

## 2. Idempotency Contract
- Каждая бизнес-операция получает `idempotency_key`.
- Повторный запрос с тем же ключом:
  - Если Transaction `COMPLETED` → вернуть успешный результат (read-only).
  - Если `FAILED` → вернуть ту же ошибку (read-only).
  - Если `PENDING` → вернуть 409 / “retry later”, без повторного side-effect.
- Новый Ledger side-effect допускается только если нет Transaction с этим ключом.

## 3. Ledger Coupling
- Ledger остаётся единственным источником баланса.
- Transaction **не** содержит ссылок на `LedgerEntry` (нет FK) — слабая связность.
- Ledger записи создаются после успешного `AccountService.transfer()` в рамках перехода `PENDING → COMPLETED`.

## 4. Transition Table

| From      | To        | Condition / Action                                              |
|-----------|-----------|-----------------------------------------------------------------|
| CREATED   | PENDING   | Начало обработки; фиксируем lock под idempotency key           |
| PENDING   | COMPLETED | AccountService.transfer + Ledger commit завершены успешно      |
| PENDING   | FAILED    | Любая ошибка (InsufficientFunds, Ledger error, etc.)           |
| *         | *         | Все остальные переходы запрещены (бросаем IllegalTransition)   |

## 5. Processing Algorithm (High-Level)
1. `transaction.atomic()` — единая DB-транзакция.
2. `SELECT ... FOR UPDATE` по `idempotency_key`.
3. Если запись существует — действуем по контракту идемпотентности (см. §2).
4. Если нет — создаём `Transaction` со статусом `CREATED`.
5. Переводим `CREATED → PENDING` (state machine проверяет допустимость).
6. Выполняем бизнес-операцию (`AccountService.transfer`).
7. В зависимости от результата: `PENDING → COMPLETED` (успех) или `PENDING → FAILED` (ошибка + сохранение error_code/message).
8. Коммит завершается атомарно; при крэше на `PENDING` повторный запрос корректно продолжит.

## 6. Crash Safety & Retries
- Если процесс падает в `PENDING`, повторный запрос увидит `PENDING` и вернёт 409 без нового side-effect.
- После перезапуска можно запустить восстановитель, который ре-триггерит зависшие `PENDING`.

## 7. Definition of Done (Stage 5)
- Один `idempotency_key` ↔ одна `Transaction`.
- Ровно один финальный статус (`COMPLETED` или `FAILED`).
- Ledger side-effects происходят не более одного раза.
- Все переходы state machine валидируются и логируют причину отказа.
- Все операции выполняются в атомарных DB-транзакциях.
