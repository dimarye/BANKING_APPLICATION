class IllegalTransitionError(Exception):
    pass


class TransactionStateMachine:
    ALLOWED_TRANSITIONS = {
        ("CREATED", "PENDING"),
        ("CREATED", "FAILED"),  # Allow early failure for fraud detection
        ("PENDING", "COMPLETED"),
        ("PENDING", "FAILED"),
    }

    TERMINAL_STATES = {"COMPLETED", "FAILED"}

    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> None:
        if from_status in cls.TERMINAL_STATES:
            raise IllegalTransitionError(
                f"Cannot transition from terminal state {from_status} to {to_status}"
            )

        if (from_status, to_status) not in cls.ALLOWED_TRANSITIONS:
            raise IllegalTransitionError(
                f"Transition from {from_status} to {to_status} is not allowed"
            )

    @classmethod
    def transition_to_pending(cls, transaction) -> None:
        cls.validate_transition(transaction.status, "PENDING")
        transaction.status = "PENDING"
        transaction.save(update_fields=["status", "updated_at"])

    @classmethod
    def transition_to_completed(cls, transaction) -> None:
        cls.validate_transition(transaction.status, "COMPLETED")
        transaction.status = "COMPLETED"
        transaction.save(update_fields=["status", "updated_at"])

    @classmethod
    def transition_to_failed(cls, transaction, error_code: str, error_message: str) -> None:
        cls.validate_transition(transaction.status, "FAILED")
        transaction.status = "FAILED"
        transaction.error_code = error_code
        transaction.error_message = error_message
        transaction.save(update_fields=["status", "error_code", "error_message", "updated_at"])
