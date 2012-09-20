
from trpycore.timezone import tz
from trnotificationsvc.gen.ttypes import Notification, NotificationPriority


class NotificationTestDataSet(object):
    """
        Convenience class to keep all Notification test data in one place.
        This class generates numerous Notifications during
        construction and makes them available via the getList()
        method.
    """
    def __init__(self):
        self.notifications_list = []
        self.single_recipients_list = []
        self.multiple_recipients_list = []

        ###############################################

        # Single recipient, plain-text msg
        n0 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test subject',
            plain_text='test plain text message body',
            html_text=''
        )
        self.notifications_list.append(n0)
        self.single_recipients_list.append(n0)

        # Single recipient, html-text msg
        n1 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-htmlTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test subject',
            plain_text='',
            html_text='<html><body><p>test notification body</p></body</html>'
        )
        self.notifications_list.append(n1)
        self.single_recipients_list.append(n1)

        # Single recipient, plain-text and html-text msg
        n2 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextAndHtmlTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test subject',
            plain_text='test plain text message body',
            html_text='<html><body><p>test notification body</p></body</html>'
        )
        self.notifications_list.append(n2)
        self.single_recipients_list.append(n2)

        ########################################

        # Multiple recipients, plain-text msg
        n3 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1,2,3],
            subject='test subject',
            plain_text='test plain text message body',
            html_text=''
        )
        self.notifications_list.append(n3)
        self.multiple_recipients_list.append(n3)




    def get_list(self):
        return self.notifications_list

    def get_single_recipients_list(self):
        return self.single_recipients_list

    def get_multiple_recipients_list(self):
        return self.multiple_recipients_list



class NotificationTestData(object):
    """ Data structure to house test notification data.
    """

    def __init__(
            self,
            not_before,
            token,
            priority,
            recipients,
            subject,
            plain_text,
            html_text):

        self.expected_not_before = not_before
        self.expected_token = token
        self.expected_priority = priority
        self.expected_recipients = recipients
        self.expected_subject = subject
        self.expected_plain_text = plain_text
        self.expected_html_text = html_text

        self.notification = Notification(
            notBefore=not_before,
            token=token,
            priority=priority,
            recipientUserIds=recipients,
            subject=subject,
            plainText=plain_text,
            htmlText=html_text
        )