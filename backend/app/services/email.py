"""Servicio de envío de emails vía SMTP (provider-agnostic)."""

import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    """True si hay configuración SMTP suficiente para enviar."""
    return bool(settings.smtp_host and settings.smtp_from)


async def send_email(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Envía un email. Devuelve True si se envió, False si SMTP no está configurado.

    Si SMTP no está configurado, loguea el contenido (útil en desarrollo).
    En cualquier error de envío, deja el log y propaga la excepción.
    """
    if not _smtp_configured():
        logger.warning(
            "SMTP no configurado. Email a %s NO enviado. Subject=%r\n%s",
            to, subject, text_body,
        )
        return False

    msg = EmailMessage()
    from_addr = (
        f"{settings.smtp_from_name} <{settings.smtp_from}>"
        if settings.smtp_from_name
        else settings.smtp_from
    )
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_start_tls,
        use_tls=settings.smtp_use_tls and not settings.smtp_start_tls,
    )
    logger.info("Email enviado a %s — subject=%r", to, subject)
    return True


async def send_verification_email(to: str, token: str) -> bool:
    """Envía el email de verificación con el link al frontend."""
    link = f"{settings.frontend_url.rstrip('/')}/verify-email?token={token}"
    subject = "Confirma tu email en MacroSnap"
    text_body = (
        "Hola,\n\n"
        "Gracias por registrarte en MacroSnap. Confirma tu correo electrónico "
        "abriendo el siguiente enlace:\n\n"
        f"{link}\n\n"
        f"El enlace caduca en {settings.verification_token_expire_hours} horas.\n\n"
        "Si no fuiste tú, ignora este mensaje.\n"
    )
    html_body = f"""<!doctype html>
<html><body style="font-family:system-ui,-apple-system,sans-serif;background:#0F0F0F;color:#fff;padding:24px">
  <div style="max-width:520px;margin:0 auto;background:#1A1A1A;border-radius:16px;padding:32px">
    <h1 style="color:#4ADE80;margin-top:0">Bienvenido a MacroSnap</h1>
    <p>Confirma tu correo electrónico para activar tu cuenta:</p>
    <p style="text-align:center;margin:32px 0">
      <a href="{link}" style="background:#4ADE80;color:#0F0F0F;padding:14px 28px;border-radius:12px;text-decoration:none;font-weight:700">
        Confirmar email
      </a>
    </p>
    <p style="color:#999;font-size:13px">
      O copia este enlace en tu navegador:<br>
      <a href="{link}" style="color:#60A5FA">{link}</a>
    </p>
    <p style="color:#666;font-size:12px;margin-top:32px">
      El enlace caduca en {settings.verification_token_expire_hours} horas.
      Si no te registraste, ignora este mensaje.
    </p>
  </div>
</body></html>"""
    return await send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)


async def send_reset_password_email(to: str, token: str) -> bool:
    """Envía el email de reset de contraseña con el link al frontend."""
    link = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
    subject = "Restablece tu contraseña en MacroSnap"
    text_body = (
        "Hola,\n\n"
        "Hemos recibido una solicitud para restablecer la contraseña de tu "
        "cuenta en MacroSnap. Abre el siguiente enlace para elegir una nueva "
        "contraseña:\n\n"
        f"{link}\n\n"
        f"El enlace caduca en {settings.reset_password_token_expire_hours} horas.\n\n"
        "Si no solicitaste este cambio, ignora este mensaje y tu contraseña "
        "seguirá siendo la misma.\n"
    )
    html_body = f"""<!doctype html>
<html><body style="font-family:system-ui,-apple-system,sans-serif;background:#0F0F0F;color:#fff;padding:24px">
  <div style="max-width:520px;margin:0 auto;background:#1A1A1A;border-radius:16px;padding:32px">
    <h1 style="color:#4ADE80;margin-top:0">Restablecer contraseña</h1>
    <p>Hemos recibido una solicitud para restablecer tu contraseña. Pulsa el botón para elegir una nueva:</p>
    <p style="text-align:center;margin:32px 0">
      <a href="{link}" style="background:#4ADE80;color:#0F0F0F;padding:14px 28px;border-radius:12px;text-decoration:none;font-weight:700">
        Restablecer contraseña
      </a>
    </p>
    <p style="color:#999;font-size:13px">
      O copia este enlace en tu navegador:<br>
      <a href="{link}" style="color:#60A5FA">{link}</a>
    </p>
    <p style="color:#666;font-size:12px;margin-top:32px">
      El enlace caduca en {settings.reset_password_token_expire_hours} horas.
      Si no solicitaste este cambio, ignora este mensaje.
    </p>
  </div>
</body></html>"""
    return await send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)
