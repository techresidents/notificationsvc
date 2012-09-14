import logging

from trpycore.thread.util import join
from trsvcscore.db.models import Notification
from trsvcscore.service.handler.service import ServiceHandler
from trnotificationsvc.gen import TNotificationService
from trnotificationsvc.gen.ttypes import Notification, NotificationPriority, UnavailableException, InvalidNotificationException

import settings
from jobmonitor import NotificationJobMonitor



class NotificationServiceHandler(TNotificationService.Iface, ServiceHandler):
    """NotificationServiceHandler manages the notification service.

    NotificationServiceHandler is responsible for managing
    the service functionality including service start,
    stop, and join.
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


    def notify(self, requestContext, notification):
        """Send notification

        Args:
            requestContext: String to identify calling context
            notification: Notification object.
        Returns:
            If no 'token' attribute was provided in the input
            notification object, the returned object will
            specify one.
        Raises:
            UnavailableException
        """
        try:
            #TODO verify this is correct
            db_session = self.get_database_session()

            # Write notification object to db to ensure we don't
            # lose the notification if this svc goes down.





            # Parse notification object, create job for each user
            # Return notification object with updated Token attribute


        except Exception as error:
            self.log.exception(error)
            raise UnavailableException(str(error))

        finally:
            db_session.close()