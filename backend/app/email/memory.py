from app.email.base import EmailMessage, EmailReceipt


class MemoryEmailSender:
    def __init__(self):
        self.deliveries: list[tuple[EmailMessage, str]] = []

    def send(self, message: EmailMessage, *, idempotency_key: str) -> EmailReceipt:
        self.deliveries.append((message, idempotency_key))
        return EmailReceipt(message_id=f"memory-{len(self.deliveries)}")
