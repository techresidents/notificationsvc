
from base import EmailProvider



class SmtpProvider(EmailProvider):
    """SmtpProvider implements the EmailProvider base class.
    """

    def __init__(
            self,
            username,
            password,
            server,
            port
    ):
        """SmtpProvider constructor.

        Args:
            username
            password
            server
            port
        """
        super(SmtpProvider, self).__init__('SmtpEmailProvider')


    def send(self, recipients, subject, plain_body, html_body):
        """
        Send an email.
        Args:
            recipients: list of email addresses
            subject: message subject
            plain_body: plain text message body
            html_body: html text message body
        """
        pass
        # TODO research python SMTP example