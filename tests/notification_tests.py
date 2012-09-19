import copy
import logging
import os
import sys
import time
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

from constants import NOTIFICATION_PRIORITY_VALUES
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
        cls.subject = 'test smtp subject'
        cls.plain_text = 'test notification body'
        cls.html_text = '<html><body><p>test notification body</p></body</html>'
        cls.notification = Notification(
            notBefore=cls.not_before,
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


    def _validate_notification_model(self, model, notification, expected_context):
        """Encapsulate code to validate a Notification model.
        Args:
            model: the Notification model to validate
            notification: the Thrift Notification the model was created from
            expected_context: the context the model was created from
        """
        self.assertIsNotNone(model.created)
        self.assertIsNotNone(model.token)
        self.assertEqual(
            NOTIFICATION_PRIORITY_VALUES[NotificationPriority._VALUES_TO_NAMES[notification.priority]],
            model.priority)
        self.assertEqual(expected_context, model.context)
        self.assertEqual(notification.subject, model.subject)
        self.assertEqual(notification.plainText, model.plain_text)
        self.assertEqual(notification.htmlText, model.html_text)
        self.assertEqual(len(notification.recipientUserIds), len(model.recipients))
        for user in model.recipients:
            self.assertIn(user.id, notification.recipientUserIds)


    def _validate_notificationjob_model(self, model, notification, expected_recipient_id, expected_retries_remaining):
        """Encapsulate code to validate a NotificationJob model.
        Args:
            model: the NotificationJob model to validate
            notification: the Thrift Notification the model was created from
            expected_recipient_id: the ID of the expected recipient
            expected_retries_remaining: the expected number of retries remaining
        """
        self.assertEqual(expected_recipient_id, model.recipient_id)
        self.assertEqual(
            NOTIFICATION_PRIORITY_VALUES[NotificationPriority._VALUES_TO_NAMES[notification.priority]],
            model.priority)
        self.assertAlmostEqual(notification.notBefore, tz.utc_to_timestamp(model.not_before), places=7)
        self.assertIsNotNone(model.created)
        self.assertIsNone(model.start)
        self.assertIsNone(model.end)
        self.assertIsNone(model.owner)
        self.assertIsNone(model.successful)
        self.assertEqual(expected_retries_remaining, model.retries_remaining)




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
            # Init to None to avoid unnecessary cleanup on failure
            updated_notification = None

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
            # Init model to None to avoid unnecessary cleanup on failure
            notification_model = None

            # Create & write Notification and NotificationJob to db
            self.service_proxy.notify(self.context, self.notification)

            # Verify Notification model
            notification_model = self.db_session.query(NotificationModel).\
                filter(NotificationModel.context==self.context).\
                filter(NotificationModel.token==self.token).\
                one()
            self._validate_notification_model(notification_model, self.notification, self.context)

            # Verify NotificationJob model
            notification_job_model = self.db_session.query(NotificationJobModel).\
                filter(NotificationJobModel.notification==notification_model).\
                one()
            self._validate_notificationjob_model(
                notification_job_model,
                self.notification,
                self.recipients[0],
                self.max_retry_attempts
            )

            # Allow processing of job to take place
            time.sleep(30)

        finally:
            if notification_model is not None:
                self._cleanup(notification_model)


    def test_notify_multiple_recipients(self):
        """Testing notification with multiple recipients.
        """

        try:
            # Init model to None to avoid unnecessary cleanup on failure
            notification_model = None

            # Write Notification and NotificationJob to db
            recipients_list = [1,2,3]
            mult_recipient_notification = copy.deepcopy(self.notification)
            mult_recipient_notification.recipientUserIds = recipients_list
            self.service_proxy.notify(self.context, mult_recipient_notification)

            # Verify Notification model
            notification_model = self.db_session.query(NotificationModel).\
                filter(NotificationModel.context==self.context).\
                filter(NotificationModel.token==self.token).\
                one()
            self._validate_notification_model(notification_model, mult_recipient_notification, self.context)

            # Verify NotificationJob model
            notification_job_models = self.db_session.query(NotificationJobModel).\
                filter(NotificationJobModel.notification==notification_model).\
                order_by(NotificationJobModel.recipient_id).\
                all()
            for index, model in enumerate(notification_job_models):
                self._validate_notificationjob_model(
                    model,
                    mult_recipient_notification,
                    recipients_list[index],
                    self.max_retry_attempts
                )

        finally:
            if notification_model is not None:
                self._cleanup(notification_model)



if __name__ == '__main__':
    unittest.main()
