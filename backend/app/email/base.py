from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str


@dataclass(frozen=True)
class EmailReceipt:
    message_id: str


class EmailDeliveryError(RuntimeError):
    def __init__(self, *, status_code: int | None, retryable: bool):
        super().__init__("Não foi possível entregar o email.")
        self.status_code = status_code
        self.retryable = retryable


class EmailSender(Protocol):
    def send(self, message: EmailMessage, *, idempotency_key: str) -> EmailReceipt: ...
