import logging

from trpycore.thread.util import join
from trsvcscore.service.handler.service import ServiceHandler
from trpersistsvc.gen import TPersistService

import settings
from jobmonitor import NotificationJobMonitor



class NotificationServiceHandler(TPersistService.Iface, ServiceHandler):
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

