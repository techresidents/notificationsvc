import socket

from default_settings import *
import providers.factory


ENV = "staging"

#Server settings
SERVER_HOST = socket.gethostname()
SERVER_INTERFACE = "0.0.0.0"
SERVER_PORT = 9095

#Service Settings
SERVICE_PID_FILE = "/opt/tr/data/%s/pid/%s.%s.pid" % (SERVICE, SERVICE, ENV)
SERVICE_JOIN_TIMEOUT = 1

#Database settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "staging_techresidents"
DATABASE_USERNAME = "techresidents"
DATABASE_PASSWORD = "techresidents"
DATABASE_CONNECTION = "postgresql+psycopg2://%s:%s@/%s?host=%s" % (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_HOST)

#Zookeeper settings
ZOOKEEPER_HOSTS = ["localhost:2181"]

#Notification svc settings
NOTIFIER_THREADS = 1
NOTIFIER_POOL_SIZE = 1
NOTIFIER_POLL_SECONDS = 60
MAX_RETRY_ATTEMPTS = 3
SECS_BETWEEN_RETRY_ATTEMPTS = 1000

# Provider Factory settings
EMAIL_PROVIDER_FACTORY = providers.factory.smtp_provider_factory

# SMTP settings
SMTP_USERNAME = 'techresidents'
SMTP_PASSWORD = 'password'
SMTP_SERVER = 'smtp.sendgrid.net'
SMTP_PORT = 587

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
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "brief_formatter",
            "stream": "ext://sys.stdout"
        },

        "file_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "long_formatter",
            "filename": "/opt/tr/data/%s/logs/%s.%s.log" % (SERVICE, SERVICE, ENV),
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
