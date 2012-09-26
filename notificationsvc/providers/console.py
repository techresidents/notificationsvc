
import logging

from base import EmailProvider



class ConsoleEmailProvider(EmailProvider):
    """ConsoleEmailProvider implements the EmailProvider
    abstract base class.

    This EmailProvider class is to be used for testing
    and prints all email data to the console.
    """

    def __init__(self, from_email):
        """SmtpProvider constructor.

        Args:
            from_email: sender's email address
        """
        super(ConsoleEmailProvider, self).__init__('ConsoleEmailProvider')
        self.from_email = from_email


    def send(self, recipient, subject, plain_text, html_text):
        """
        Print an email.
        Args:
            recipient: recipient's email address
            subject: message subject
            plain_body: plain text message body
            html_body: html text message body

        """
        try:
            print '\n'
            print 'From: %s' % self.from_email
            print 'To: %s' % recipient
            print 'Subject: %s' % subject
            print 'Plain Text: %s' % plain_text
            print 'HTML Text: %s' % html_text
            print '\n'

        except Exception as e:
            logging.exception(e)
            raise e

