
import abc

class NotificationProvider(object):
    """NotificationProvider abstract base class.

    Base class for concrete notification provider implementations
    such as EmailProviders, SMSProviders, etc.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        """NotificationProvider constructor.

        Args:
            name: string for the name of the provider
        """
        self.name = name



class EmailProvider(NotificationProvider):
    """EmailProvider abstract base class.

    Base class for concrete email provider implementations.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        """EmailProvider constructor.

        Args:
            name: string for the name of the provider
        """
        super(EmailProvider, self).__init__(name)

    def send(self, recipients, subject, plain_text, html_text):
        """Send email.
        Args:
            recipients:
            subject:
            plain_text,
            html_text
        """
        return


class SmsProvider(NotificationProvider):
    """SmsProvider abstract base class.

    Base class for concrete SMS provider implementations.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        """SmsProvider constructor.

        Args:
            name: string for the name of the provider
        """
        super(SmsProvider, self).__init__(name)