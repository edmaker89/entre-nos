from html import escape

from app.email.base import EmailMessage


def password_reset_email(to: str, name: str, url: str) -> EmailMessage:
    safe_name = escape(name)
    safe_url = escape(url, quote=True)
    return EmailMessage(
        to=to,
        subject="Redefina sua senha — Entre Nós",
        text=(
            f"Olá, {name}.\n\n"
            "Recebemos uma solicitação para redefinir sua senha. "
            f"Use este link em até 15 minutos:\n{url}\n\n"
            "Se você não fez a solicitação, ignore este email."
        ),
        html=(
            f"<p>Olá, {safe_name}.</p>"
            "<p>Recebemos uma solicitação para redefinir sua senha.</p>"
            f'<p><a href="{safe_url}">Redefinir senha</a></p>'
            "<p>O link expira em 15 minutos. Se você não fez a solicitação, ignore este email.</p>"
        ),
    )
