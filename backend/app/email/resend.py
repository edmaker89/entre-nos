import httpx

from app.email.base import EmailDeliveryError, EmailMessage, EmailReceipt


class ResendEmailSender:
    endpoint = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: str,
        sender: str,
        timeout_seconds: float,
        *,
        client: httpx.Client | None = None,
    ):
        self.api_key = api_key
        self.sender = sender
        self.timeout_seconds = timeout_seconds
        self.client = client or httpx.Client()

    def send(self, message: EmailMessage, *, idempotency_key: str) -> EmailReceipt:
        try:
            response = self.client.post(
                self.endpoint,
                json={
                    "from": self.sender,
                    "to": [message.to],
                    "subject": message.subject,
                    "text": message.text,
                    "html": message.html,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": idempotency_key,
                },
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise EmailDeliveryError(status_code=None, retryable=True) from exc

        if 200 <= response.status_code < 300:
            try:
                message_id = response.json()["id"]
            except (KeyError, TypeError, ValueError):
                raise EmailDeliveryError(
                    status_code=response.status_code, retryable=False
                ) from None
            return EmailReceipt(message_id=message_id)

        name = None
        if response.status_code == 409:
            try:
                name = response.json().get("name")
            except (TypeError, ValueError):
                pass
        raise EmailDeliveryError(
            status_code=response.status_code,
            retryable=response.status_code >= 500 or name == "concurrent_idempotent_requests",
        )
