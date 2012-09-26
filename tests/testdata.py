
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
            subject='test plain text subject',
            plain_text='test message body',
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
            subject='test html text subject',
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
            subject='test multipart subject',
            plain_text='test message body',
            html_text='<html><body><p>test notification body</p></body</html>'
        )
        self.notifications_list.append(n2)
        self.single_recipients_list.append(n2)

        # Single recipient, plain-text msg, high priority
        n3 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextMsg-highPriority',
            priority=NotificationPriority.HIGH_PRIORITY,
            recipients=[1],
            subject='test high priority message',
            plain_text='test message body',
            html_text=''
        )
        self.notifications_list.append(n3)
        self.single_recipients_list.append(n3)

        # Single recipient, plain-text msg, low priority
        n4 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextMsg-lowPriority',
            priority=NotificationPriority.LOW_PRIORITY,
            recipients=[1],
            subject='test low priority message',
            plain_text='test message body',
            html_text=''
        )
        self.notifications_list.append(n4)
        self.single_recipients_list.append(n4)

        # Single recipient, plain text msg with template strings
        n5 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTexttMsg-templates',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test plain text msg to ${first_name} ${last_name}',
            plain_text='Dear ${first_name} ${last_name}, test message body with',
            html_text=''
        )
        self.notifications_list.append(n5)
        self.single_recipients_list.append(n5)

        # Single recipient, html-text msg with template strings
        n6 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-htmlTextMsg-templates',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test html text msg to ${first_name} ${last_name}',
            plain_text='',
            html_text='<html><body><p>Dear ${first_name} ${last_name}, test notification body</p></body</html>'
        )
        self.notifications_list.append(n6)
        self.single_recipients_list.append(n6)

        # Single recipient, multi-part msg with template strings
        n7 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextAndHtmlTextMsg-templates',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1],
            subject='test multipart msg to ${first_name} ${last_name}',
            plain_text='Dear ${first_name} ${last_name}, test message body with',
            html_text='<html><body><p>Dear ${first_name} ${last_name}, test notification body</p></body</html>'
        )
        self.notifications_list.append(n7)
        self.single_recipients_list.append(n7)

        ########################################

        # Multiple recipients, plain-text msg
        n8 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1,2,3],
            subject='test plain text subject',
            plain_text='test message body',
            html_text=''
        )
        self.notifications_list.append(n8)
        self.multiple_recipients_list.append(n8)

        # Multiple recipient, html-text msg
        n9 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-htmlTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[1, 2],
            subject='test html text subject',
            plain_text='',
            html_text='<html><body><p>test notification body</p></body</html>'
        )
        self.notifications_list.append(n9)
        self.multiple_recipients_list.append(n9)

        # Multiple recipient, plain-text and html-text msg
        n10 = NotificationTestData(
            not_before=tz.timestamp(),
            token='singleRecipient-plainTextAndHtmlTextMsg',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipients=[3, 4, 5],
            subject='test multipart subject',
            plain_text='test message body',
            html_text='<html><body><p>test notification body</p></body</html>'
        )
        self.notifications_list.append(n10)
        self.multiple_recipients_list.append(n10)



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