
import settings
from providers.console import ConsoleEmailProvider
from providers.smtp import SmtpProvider


def smtp_provider_factory():
    """Returns an SMTP Provider object.

    This factory returns an SMTP Provider
    whose attributes are derived from
    the notification settings.
    """
    return SmtpProvider(
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        from_email=settings.EMAIL_PROVIDER_FROM_EMAIL,
        use_tls=settings.SMTP_USE_TLS
    )

def console_email_provider_factory():
    """Returns a Console EmailProvider object.

    This factory returns a Console EmailProvider
    that prints all email msg data to the
    console.
    """
    return ConsoleEmailProvider(
        from_email=settings.EMAIL_PROVIDER_FROM_EMAIL,
    )

def send_grid_smtp_provider_factory():
    """ TODO in the future, if needed.

    return SendGridSmtpProvider(
       username=settings.SEND_GRID_USERNAME,
       password=settings.SEND_GRID_PASSWORD,
       server=settings.SEND_GRID_SERVER,
       port=settings.SEND_GRID_PORT,
       custom_headers=SEND_GRID_CUSTOM_HEADERS,
       filter_settings=SEND_GRID_FILTERS,
       unique_arguments=SEND_GRID_UNIQUE_ARGS,
    )
    """
    pass