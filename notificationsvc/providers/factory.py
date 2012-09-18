
import settings
from providers.smtp import SmtpProvider


def smtp_provider_factory():
    return SmtpProvider(
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        server=settings.SMTP_SERVER,
        port=settings.SMTP_PORT
    )
