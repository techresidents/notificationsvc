import os
import socket

import providers.factory


ENV = os.getenv("SERVICE_ENV", "default")

#Service Settings
SERVICE = "notificationsvc"
SERVICE_PID_FILE = "%s.%s.pid" % (SERVICE, ENV)
SERVICE_JOIN_TIMEOUT = 1

#Server settings
THRIFT_SERVER_ADDRESS = socket.gethostname()
THRIFT_SERVER_INTERFACE = "0.0.0.0"
THRIFT_SERVER_PORT = 9095

#Database settings
DATABASE_HOST = "localdev"
DATABASE_NAME = "localdev_techresidents"
DATABASE_USERNAME = "techresidents"
DATABASE_PASSWORD = "techresidents"
DATABASE_CONNECTION = "postgresql+psycopg2://%s:%s@/%s?host=%s" % (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_HOST)

#Zookeeper settings
ZOOKEEPER_HOSTS = ["localdev:2181"]

#Notification svc settings
NOTIFIER_THREADS = 1
NOTIFIER_POOL_SIZE = 1
NOTIFIER_POLL_SECONDS = 60
NOTIFIER_JOB_RETRY_SECONDS = 300
NOTIFIER_JOB_MAX_RETRY_ATTEMPTS = 3


# Provider Factory settings
EMAIL_PROVIDER_FACTORY = providers.factory.console_email_provider_factory
EMAIL_PROVIDER_FROM_EMAIL = 'Tech Residents Support <support@techresidents.com>'

# SMTP settings
SMTP_USERNAME = None
SMTP_PASSWORD = None
SMTP_HOST = 'localhost'
SMTP_PORT = 25
SMTP_USE_TLS = False



#Logging settings
LOGGING = {
    "version": 1,

    "formatters": {
        "brief_formatter": {
            "format": "%(levelname)s: %(message)s"
        },

        "long_formatter": {
            "format": "%(asctime)s %(levelname)s: %(name)s %(message)s"
        }
    },

    "handlers": {

        "console_handler": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "brief_formatter",
            "stream": "ext://sys.stdout"
        },

        "file_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "long_formatter",
            "filename": "%s.%s.log" % (SERVICE, ENV),
            "when": "midnight",
            "interval": 1,
            "backupCount": 7
        }
    },
    
    "root": {
        "level": "DEBUG",
        "handlers": ["console_handler", "file_handler"]
    }
}
