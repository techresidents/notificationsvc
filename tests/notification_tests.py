import os
import sys
import unittest

SERVICE_NAME = "notificationsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trpycore.timezone import tz
from trsvcscore.db.models import ChatMinute

from trnotificationsvc.gen.ttypes import Notification, NotificationPriority, UnavailableException, InvalidNotificationException
from testbase import IntegrationTestCase

class NotificationTest(IntegrationTestCase):
    """
        Test the Notification Service interface.
    """

    @classmethod
    def setUpClass(cls):
        IntegrationTestCase.setUpClass()

        cls.context = 'testContext'
        cls.notification = Notification(
            token='testToken',
            priority=NotificationPriority.DEFAULT_PRIORITY,
            recipientUserIds=['0'],
            subject='testSubject',
            plainText='testNotificationBody'
        )


    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()

    def test_notify_invalidNotification(self):

        # Invalid context
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(None, self.notification)

        # Invalid priority
        invalid_notification = self.notification
        invalid_notification.priority = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid subject
        invalid_notification = self.notification
        invalid_notification.subject = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid recipients
        invalid_notification = self.notification
        invalid_notification.recipientUserIds = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid notification body
        invalid_notification = self.notification
        invalid_notification.plainText = None
        invalid_notification.htmlText = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)


if __name__ == '__main__':
    unittest.main()
