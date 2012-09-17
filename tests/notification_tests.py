import copy
import logging
import os
import sys
import unittest

SERVICE_NAME = "notificationsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trnotificationsvc.gen.ttypes import Notification, NotificationPriority, UnavailableException, InvalidNotificationException
from trpycore.timezone import tz
from trsvcscore.db.models.notification_models import Notification as NotificationModel
from trsvcscore.db.models.notification_models import NotificationJob as NotificationJobModel
from trsvcscore.db.models.notification_models import NotificationUser as NotificationUserModel

from constants import NOTIFICATION_PRIORITY_TYPE_IDS
from testbase import IntegrationTestCase

import settings




class NotificationTest(IntegrationTestCase):
    """
        Test the Notification Service interface.
    """

    @classmethod
    def setUpClass(cls):
        IntegrationTestCase.setUpClass()

        try:
            cls.db_session = cls.service.handler.get_database_session()
        except Exception as e:
            logging.exception(e)
            cls.db_session.close()
            raise e

        cls.priority = NotificationPriority.DEFAULT_PRIORITY
        cls.max_retry_attempts = settings.MAX_RETRY_ATTEMPTS
        cls.not_before = tz.timestamp()
        cls.context = 'testContext'
        cls.token = 'testToken'
        cls.recipients = [1] # list of user IDs
        cls.subject = 'testSubject'
        cls.plain_text = 'testNotificationBody'
        cls.html_text = 'testNotificationBody'
        cls.notification = Notification(
            token=cls.token,
            priority=cls.priority,
            recipientUserIds=cls.recipients,
            subject=cls.subject,
            plainText=cls.plain_text,
            htmlText=cls.html_text
        )


    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()
        cls.db_session.close()


    def _get_notification_model(self, context, notification):
        """Get Notification object from db

        Args:
            context: context string
            notification: Thrift Notification object
        Returns:
            SqlAlchemy Notification object
        Throws:
            Exception if model doesn't exist

        """
        try:
            notification_model = self.db_session.query(NotificationModel).\
                filter(NotificationModel.context==context).\
                filter(NotificationModel.token==notification.token).\
                one()
            return notification_model
        except Exception as e:
            logging.exception(e)
            raise e

    def _cleanup(self, notification_model):
        """Delete notification from db.

        Pass in either the Thrift Notification object
        or the sqlalchemy Notification object.

        This convenience method also deletes any
        associated notification jobs and users.

        Args:
            notification: Thrift notification object
            notification_model: Notification sqlalchemy object

        """
        try:
            # Clean up notification jobs
            job_models = self.db_session.query(NotificationJobModel).\
                filter(NotificationJobModel.notification==notification_model).\
                all()
            for model in job_models:
                self.db_session.delete(model)

            # Clean up notification_users
            notification_user_models = self.db_session.query(NotificationUserModel).\
                filter(NotificationUserModel.notification==notification_model).\
                all()
            for model in notification_user_models:
                self.db_session.delete(model)

            # Clean up notification
            self.db_session.delete(notification_model)

            self.db_session.commit()

        except Exception as e:
            logging.exception(e)
            self.db_session.rollback()
            self.db_session.close()
            raise e


    def test_notify_invalidNotification(self):

        # Invalid context
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(None, self.notification)

        # Invalid priority
        invalid_notification = copy.deepcopy(self.notification)
        invalid_notification.priority = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid subject
        invalid_notification = copy.deepcopy(self.notification)
        invalid_notification.subject = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid recipients
        invalid_notification = copy.deepcopy(self.notification)
        invalid_notification.recipientUserIds = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid notification body
        invalid_notification = copy.deepcopy(self.notification)
        invalid_notification.plainText = None
        invalid_notification.htmlText = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)


    def test_notify_tokenGeneration(self):
        try:
            no_token_notification = copy.deepcopy(self.notification)
            no_token_notification.token = None
            updated_notification = self.service_proxy.notify(self.context, no_token_notification)
            self.assertIsNotNone(updated_notification.token)
        finally:
            if updated_notification is not None:
                self._cleanup(self._get_notification_model(self.context, updated_notification))


    def test_notify_single_recipient(self):
        """Simple test case.

        Test a notification with one intended recipient
        """

        try:
            # Write Notification and NotificationJob to db
            self.service_proxy.notify(self.context, self.notification)

            # Verify Notification model
            notification_model = self.db_session.query(NotificationModel).\
                filter(NotificationModel.context==self.context).\
                filter(NotificationModel.token==self.token).\
                one()
            self.assertIsNotNone(notification_model.created)
            self.assertEqual(len(self.recipients), len(notification_model.recipients))
            self.assertEqual(self.recipients[0], notification_model.recipients[0].id)
            self.assertEqual(self.subject, notification_model.subject)
            self.assertEqual(self.plain_text, notification_model.plain_text)
            self.assertEqual(self.html_text, notification_model.html_text)

            # Verify NotificationJob model
            notification_job_model = self.db_session.query(NotificationJobModel).\
                filter(NotificationJobModel.notification==notification_model).\
                one()
            self.assertEqual(self.recipients[0], notification_job_model.recipient_id)
            self.assertEqual(
                NOTIFICATION_PRIORITY_TYPE_IDS[NotificationPriority._VALUES_TO_NAMES[self.priority]],
                notification_job_model.priority_id)
            self.assertAlmostEqual(self.not_before, tz.utc_to_timestamp(notification_job_model.not_before), places=0) #round to nearest full second
            self.assertIsNotNone(notification_job_model.created)
            self.assertIsNone(notification_job_model.start)
            self.assertIsNone(notification_job_model.end)
            self.assertIsNone(notification_job_model.owner)
            self.assertIsNone(notification_job_model.successful)
            self.assertEqual(self.max_retry_attempts, notification_job_model.retries_remaining)

        finally:
            if notification_model is not None:
                self._cleanup(notification_model)


    def test_notify_multiple_recipients(self):
        """Testing notification with multiple recipients
        """
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
