import logging
import uuid

from sqlalchemy.sql import func

from trpycore.factory.base import Factory
from trpycore.pool.queue import QueuePool
from trpycore.thread.util import join
from trpycore.timezone import tz
from trsvcscore.db.models.notification_models import Notification as NotificationModel
from trsvcscore.db.models.notification_models import NotificationJob as NotificationJobModel
from trsvcscore.db.models.django_models import User
from trsvcscore.service.handler.service import ServiceHandler
from trnotificationsvc.gen import TNotificationService
from trnotificationsvc.gen.ttypes import NotificationPriority, UnavailableException, InvalidNotificationException

import settings

from constants import NOTIFICATION_PRIORITY_VALUES
from jobmonitor import NotificationJobMonitor, NotificationThreadPool
from notifier import Notifier


class NotificationServiceHandler(TNotificationService.Iface, ServiceHandler):
    """NotificationServiceHandler manages the notification service.

    This class specifies the service interface.
    It is also responsible for managing the service
    functionality including service start, stop,
    and join.

    """
    def __init__(self, service):
        super(NotificationServiceHandler, self).__init__(
		    service,
            zookeeper_hosts=settings.ZOOKEEPER_HOSTS,
            database_connection=settings.DATABASE_CONNECTION)

        self.log = logging.getLogger("%s.%s" % (__name__, NotificationServiceHandler.__name__))

        # Create pool of Notifier objects which will do the
        # actual work of sending notifications
        def notifier_factory():
            return Notifier(
                db_session_factory=self.get_database_session,
                email_provider=settings.EMAIL_PROVIDER_FACTORY(),
                job_retry_seconds=settings.NOTIFIER_JOB_RETRY_SECONDS
            )
        self.notifier_pool = QueuePool(
            size=settings.NOTIFIER_POOL_SIZE,
            factory=Factory(notifier_factory))

        # Create pool of threads to manage the work
        self.thread_pool = NotificationThreadPool(
            num_threads=settings.NOTIFIER_THREADS,
            notifier_pool=self.notifier_pool)

        # Create job monitor which scans for new jobs
        # to process and delegates to the thread pool
        self.job_monitor = NotificationJobMonitor(
            db_session_factory=self.get_database_session,
            thread_pool=self.thread_pool,
            poll_seconds=settings.NOTIFIER_POLL_SECONDS)



    def start(self):
        """Start handler."""
        super(NotificationServiceHandler, self).start()
        self.thread_pool.start()
        self.job_monitor.start()

    def stop(self):
        """Stop handler."""
        self.job_monitor.stop()
        self.thread_pool.stop()
        super(NotificationServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.thread_pool, self.job_monitor, super(NotificationServiceHandler, self)], timeout)


    def _validate_notify_params(self, db_session, users, context, notification):
        """Validate input params of the notify() method

        As a performance optimization, when this method validates
        each recipient user ID it will append the User to the input
        users list.
        """
        if not context:
            raise InvalidNotificationException('Invalid context')

        if notification.priority != NotificationPriority.DEFAULT_PRIORITY and\
            notification.priority != NotificationPriority.LOW_PRIORITY and\
            notification.priority != NotificationPriority.HIGH_PRIORITY:
            raise InvalidNotificationException('Invalid priority')

        if not notification.subject:
            raise InvalidNotificationException('Invalid subject')

        if (not notification.htmlText) and (not notification.plainText):
            raise InvalidNotificationException('Invalid body')

        if notification.recipientUserIds is None or\
            len(notification.recipientUserIds) <= 0:
            raise InvalidNotificationException('Invalid recipients')

        try:
            # Ensure the specified recipients exist
            for user_id in notification.recipientUserIds:
                user = db_session.query(User).filter(User.id==user_id).one()
                users.append(user)
        except Exception as e:
            raise InvalidNotificationException('Invalid user')



    def notify(self, context, notification):
        """Send notification

        This method writes the input notification to the db
        and creates a job for each recipient for the
        notification to process.
        This is done to ensure that we don't lose any
        information should this service go down.

        Args:
            context: String to identify calling context
            notification: Notification object.
        Returns:
            Thrift Notification object.
            If no 'token' attribute was provided in the input
            notification object, the returned object will
            specify one.
        Raises:
            InvalidNotificationException if input Notification
            object is invalid.
            UnavailableException for any other unexpected error.
        """

        try:

            # Get a db session
            db_session = self.get_database_session()

            # Validate inputs
            users = []
            self._validate_notify_params(db_session, users, context, notification)

            # If input notification doesn't specify a
            # unique token, then generate one.
            if not notification.token:
                notification.token = uuid.uuid4().hex

            # Create Notification Model
            notification_model = NotificationModel(
                created=func.current_timestamp(),
                token=notification.token,
                context=context,
                priority=NOTIFICATION_PRIORITY_VALUES[
                         NotificationPriority._VALUES_TO_NAMES[notification.priority]],
                recipients=users,
                subject=notification.subject,
                html_text=notification.htmlText,
                plain_text=notification.plainText
            )
            db_session.add(notification_model)

            # If notification specified a start-processing-time
            # convert it to UTC DateTime object.
            if notification.notBefore is not None:
                processing_start_time = tz.timestamp_to_utc(notification.notBefore)
            else:
                processing_start_time = func.current_timestamp()

            # Create NotificationJobs
            for user_id in notification.recipientUserIds:
                job = NotificationJobModel(
                    created=func.current_timestamp(),
                    not_before=processing_start_time,
                    notification=notification_model,
                    recipient_id=user_id,
                    priority=NOTIFICATION_PRIORITY_VALUES[
                             NotificationPriority._VALUES_TO_NAMES[notification.priority]],
                    retries_remaining=settings.NOTIFIER_JOB_MAX_RETRY_ATTEMPTS
                )
                db_session.add(job)

            db_session.commit()

            return notification

        except InvalidNotificationException as error:
            self.log.exception(error)
            raise InvalidNotificationException()
        except Exception as error:
            self.log.exception(error)
            raise UnavailableException(str(error))

        finally:
            db_session.close()