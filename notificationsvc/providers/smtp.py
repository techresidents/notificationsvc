
import logging
import smtplib

from cStringIO import StringIO
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.generator import Generator

from base import EmailProvider
from exceptions import InvalidParameterException



class SmtpProvider(EmailProvider):
    """SmtpProvider implements the EmailProvider base class.

    This EmailProvider class is responsible for establishing
    and maintaining a connection to a SMTP server.

    It is responsible for any throttling that needs to occur.
    """

    # Hard code UTF-8 in one place
    UTF8 = 'utf-8'


    def __init__(
            self,
            username,
            password,
            host,
            port,
            from_email,
            use_tls=True
    ):
        """SmtpProvider constructor.

        Args:
            username:
            password:
            server:
            port:
            from_email:
            use_tls:
        """
        super(SmtpProvider, self).__init__('SmtpEmailProvider')
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.use_tls = False # TODO change back to _use_tls after testing
        self.from_email = from_email
        self.connection = None


    def _build_message(self, recipient_email, subject, plain_text, html_text):
        """ Method to construct an Email message

        Args:
            recipient_email: recipient's email address
            subject:
            plain_text:
            html_text:
        Returns:
            Returns a flattened MIMEMultipart object. This output can be
            used directly with smtplib.
        """

        if plain_text and html_text:
            # Create multipart message container - the correct MIME type is multipart/alternative.
            msg = MIMEMultipart('alternative')
            msg.set_charset(SmtpProvider.UTF8) # this has to be set before anything else is done
            plain_part = MIMEText(plain_text, 'plain', SmtpProvider.UTF8)
            html_part = MIMEText(html_text, 'html', SmtpProvider.UTF8)

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message,
            # is best and preferred.
            msg.attach(plain_part)
            msg.attach(html_part)

        elif plain_text:
            msg = MIMEText(plain_text, 'plain', SmtpProvider.UTF8)
            msg.set_charset(SmtpProvider.UTF8)
        elif html_text:
            msg = MIMEText(html_text, 'html', SmtpProvider.UTF8)
            msg.set_charset(SmtpProvider.UTF8)


        msg['Subject'] = Header(subject, SmtpProvider.UTF8)
        # TODO Note that if we start including names in the 'to' and 'from'
        # fields below (e.g. 'Brian Mullins <bmullins@techresidents.com>',
        # the name portion should be UTF8 encoded using
        # a Header object, as the subject is doing.
        msg['From'] = self.from_email
        msg['To'] = recipient_email

        # Instantiate a Generator object to flatten the multipart
        # object to a string. Using multipart.as_string() escapes
        # "From" lines.
        msg_str = StringIO()
        generator = Generator(msg_str, mangle_from_=False)
        generator.flatten(msg)

        return msg_str.getvalue()


    def _open(self):
        """ Open connection to server
        """
        if self.connection is None:

            self.connection = smtplib.SMTP(
                host=self.host,
                port=self.port
            )

            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)


    def _close(self):
        """ Close connection to server
        """
        try:
            if self.connection:
                self.connection.quit()
        except Exception as e:
            logging.exception(e)

        self.connection = None


    def _validate_send_params(self, recipient, subject, plain_text, html_text):
        """ Encapsulating logic that validates inputs of the send() method.

        Args:
            recipient: recipient email address
            subject: email subject
            plain_text: email plain text
            html_text: email html text
        Raises:
            InvalidParameterException
        """
        if not recipient:
            raise InvalidParameterException
        if not subject:
            raise InvalidParameterException
        if (not plain_text) and not (html_text):
            raise InvalidParameterException


    def send(self, recipient, subject, plain_text, html_text):
        """
        Send an email.
        Args:
            recipient: recipient's email address
            subject: message subject
            plain_body: plain text message body
            html_body: html text message body
        Raises:
            InvalidParameterException if any of the
                input parameters are invalid

        """
        try:
            print '****************'
            print 'sending email'
            print '****************'
            self._validate_send_params(recipient, subject, plain_text, html_text)
            msg = self._build_message(recipient, subject, plain_text, html_text)
            self._open()
            self.connection.sendmail(
                self.from_email,
                recipient,
                msg
            )

        except InvalidParameterException as e:
            raise e
        except Exception as e:
            logging.exception(e)
            raise e

        finally:
            self._close()
