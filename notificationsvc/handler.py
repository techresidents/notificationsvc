import logging
import uuid

from trpycore.thread.util import join
from trpycore.timezone import tz
from trsvcscore.db.models.notification_models import Notification as NotificationModel
from trsvcscore.db.models.notification_models import  NotificationUser, NotificationJob
from trsvcscore.db.models.django_models import User
from trsvcscore.service.handler.service import ServiceHandler
from trnotificationsvc.gen import TNotificationService
from trnotificationsvc.gen.ttypes import Notification, NotificationPriority, UnavailableException, InvalidNotificationException

import settings

from constants import NOTIFICATION_PRIORITY_TYPE_IDS
from jobmonitor import NotificationJobMonitor



class NotificationServiceHandler(TNotificationService.Iface, ServiceHandler):
    """NotificationServiceHandler manages the notification service.

    NotificationServiceHandler specifies the service
    interface.

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

        # Create job monitor which scans for new jobs
        # to process and delegates the real work.
        self.job_monitor = NotificationJobMonitor(
                settings.NOTIFIER_THREADS,
                self.get_database_session,
                settings.NOTIFIER_POLL_SECONDS)
    
    def start(self):
        """Start handler."""
        super(NotificationServiceHandler, self).start()
        self.job_monitor.start()

    def stop(self):
        """Stop handler."""
        self.job_monitor.stop()
        super(NotificationServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.job_monitor, super(NotificationServiceHandler, self)], timeout)


    def _validate_notify_params(self, db_session, users, context, notification):
        """Validate input params of the notify() method

        As a performance optimization, when this method validates
        each recipient user ID it will append the User to the input
        users list.
        """
        if not context:
            raise InvalidNotificationException()

        if not isinstance(notification.priority, NotificationPriority):
            raise InvalidNotificationException()

        if not notification.subject:
            raise InvalidNotificationException()

        if (not notification.htmlText) and (not notification.plainText):
            raise InvalidNotificationException()

        if not len(notification.recipientUserIds):
            raise InvalidNotificationException()

        try:
            # Ensure the specified recipients exist
            for user_id in notification.recipientUserIds:
                user = db_session.query(User).filter(User.id==user_id).one()
                users.append(user)
        except Exception:
            raise InvalidNotificationException()



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
                token=notification.token,
                context=context,
                users=users,
                subject=notification.subject,
                html_text=notification.htmlText,
                plain_text=notification.plainText
            )
            db_session.add(notification_model)

            # If notification specified a start-processing-time
            # convert it to UTC DateTime object.
            processing_start_time = None
            if notification.notBefore is not None:
                processing_start_time = tz.timestamp_to_utc(notification.notBefore)

            # Create NotificationJobs
            for user_id in notification.recipientUserIds:
                job = NotificationJob(
                    not_before=processing_start_time,
                    notification=notification_model,
                    recipient_id=user_id,
                    priority=NOTIFICATION_PRIORITY_TYPE_IDS[
                             NotificationPriority._VALUES_TO_NAMES[notification.priority]],
                    retries_remaining=settings.MAX_RETRY_ATTEMPTS
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