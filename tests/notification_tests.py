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
from testdata import NotificationTestDataSet, NotificationTestData

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

        # Test Notification data
        cls.test_data_set = NotificationTestDataSet()
        cls.test_notifications_list = cls.test_data_set.get_list()

        # Test NotificationJob data
        cls.context = 'testContext'
        cls.max_retry_attempts = settings.MAX_RETRY_ATTEMPTS


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

    def _cleanup_models(self, notification_models):
        """ Delete notification models from db.
         Args:
            notification_models: list of notification models
        """
        for model in notification_models:
            self._cleanup_model(model)

    def _cleanup_model(self, notification_model):
        """Delete notification from db.

        This convenience method deletes any
        associated notification jobs and users.

        Args:
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

            # Commit changes to db
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

        # Get a test Notification object
        notification_test_data = self.test_notifications_list[0]
        notification = notification_test_data.notification

        # Invalid context
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(None, notification)

        # Invalid priority
        invalid_notification = copy.deepcopy(notification)
        invalid_notification.priority = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid subject
        invalid_notification = copy.deepcopy(notification)
        invalid_notification.subject = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid recipients
        invalid_notification = copy.deepcopy(notification)
        invalid_notification.recipientUserIds = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)

        # Invalid notification body
        invalid_notification = copy.deepcopy(notification)
        invalid_notification.plainText = None
        invalid_notification.htmlText = None
        with self.assertRaises(InvalidNotificationException):
            self.service_proxy.notify(self.context, invalid_notification)


    def test_notify_tokenGeneration(self):
        try:
            # Init to None to avoid unnecessary cleanup on failure
            updated_notification = None

            # Get a test notification object
            notification_test_data = self.test_notifications_list[0]
            notification = notification_test_data.notification

            # Copy object before modification
            no_token_notification = copy.deepcopy(notification)
            no_token_notification.token = None
            updated_notification = self.service_proxy.notify(self.context, no_token_notification)
            self.assertIsNotNone(updated_notification.token)

        finally:
            if updated_notification is not None:
                self._cleanup_model(self._get_notification_model(self.context, updated_notification))


    def test_notify_single_recipient(self):
        """Simple test case.

        Test a notification with one intended recipient
        """

        try:
            # Init models to None to avoid unnecessary cleanup on failure
            notification_models = None

            # Test notify() with various Notification objects as inputs
            for test_notification in self.test_data_set.get_single_recipients_list():

                # Create & write Notification and NotificationJob to db
                self.service_proxy.notify(self.context, test_notification.notification)

                # Verify Notification model
                notification_model = self.db_session.query(NotificationModel).\
                    filter(NotificationModel.context==self.context).\
                    filter(NotificationModel.token==test_notification.expected_token).\
                    one()
                self._validate_notification_model(notification_model, test_notification.notification, self.context)

                # Verify NotificationJob model
                notification_job_model = self.db_session.query(NotificationJobModel).\
                    filter(NotificationJobModel.notification==notification_model).\
                    one()
                self._validate_notificationjob_model(
                    notification_job_model,
                    test_notification.notification,
                    test_notification.expected_recipients[0], # only 1 recipient in these tests
                    self.max_retry_attempts
                )

                # Add model to list for cleanup
                if notification_models is None:
                    notification_models = []
                else:
                    notification_models.append(notification_model)


            # Allow processing of job to take place
            time.sleep(30)


        finally:
            if notification_models is not None:
                self._cleanup_models(notification_models)


    def test_notify_multiple_recipients(self):
        """Testing notification with multiple recipients.
        """

        try:
            # Init models to None to avoid unnecessary cleanup on failure
            notification_models = None

            # Test notify() with various Notification objects as inputs
            for test_notification in self.test_data_set.get_multiple_recipients_list():

                # Write Notification and NotificationJob to db
                self.service_proxy.notify(self.context, test_notification.notification)

                # Verify Notification model
                notification_model = self.db_session.query(NotificationModel).\
                    filter(NotificationModel.context==self.context).\
                    filter(NotificationModel.token==test_notification.expected_token).\
                    one()
                self._validate_notification_model(notification_model, test_notification.notification, self.context)

                # Verify NotificationJob model
                notification_job_models = self.db_session.query(NotificationJobModel).\
                    filter(NotificationJobModel.notification==notification_model).\
                    order_by(NotificationJobModel.recipient_id).\
                    all()
                for index, model in enumerate(notification_job_models):
                    self._validate_notificationjob_model(
                        model,
                        test_notification.notification,
                        test_notification.expected_recipients[index],
                        self.max_retry_attempts
                    )

                # Add model to list for cleanup
                if notification_models is None:
                    notification_models = []
                else:
                    notification_models.append(notification_model)


            # Allow processing of job to take place
            time.sleep(30)


        finally:
            if notification_models is not None:
                self._cleanup_models(notification_models)




if __name__ == '__main__':
    unittest.main()
