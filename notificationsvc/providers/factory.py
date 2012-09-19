
import settings
from providers.smtp import SmtpProvider


def smtp_provider_factory():
    return SmtpProvider(
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        from_email=settings.EMAIL_PROVIDER_FROM_EMAIL,
        use_tls=settings.SMTP_USE_TLS
    )


def send_grid_smtp_provider_factory():
    # return SendGridSmtpProvider(
    #   username=settings.SEND_GRID_USERNAME,
    #   password=settings.SEND_GRID_PASSWORD,
    #   server=settings.SEND_GRID_SERVER,
    #   port=settings.SEND_GRID_PORT,
    #   custom_headers=SEND_GRID_CUSTOM_HEADERS,
    #   filter_settings=SEND_GRID_FILTERS,
    #   unique_arguments=SEND_GRID_UNIQUE_ARGS,
    #)
    pass