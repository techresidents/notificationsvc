
import logging
import threading
import time

from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.db.models import NotificationJob
from trsvcscore.db.job import DatabaseJob, DatabaseJobQueue, JobOwned, QueueEmpty, QueueStopped

from notifier import Notifier



class NotificationThreadPool(ThreadPool):
    """Thread pool used to process notifications.

    Given a work item (job_id), this class will process the
    job and delegate the work to send a notification.
    """
    def __init__(self, num_threads, db_session_factory):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            db_session_factory: callable returning new sqlalchemy
                db session.
        """
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        super(NotificationThreadPool, self).__init__(num_threads)

    def process(self, database_job):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (job) is put on the queue.

        Args:
            database_job: DatabaseJob object, or objected derived from DatabaseJob
        """
        #TODO consider pool of Notifiers to limit number of Notifier objects
        notifier = Notifier(self.db_session_factory)
        notifier.send(database_job)


class NotificationJobMonitor(object):
    """
    NotificationJobMonitor monitors for new notification jobs, and delegates
     work items to the NotificationThreadPool.
    """
    def __init__(self, num_threads, db_session_factory, poll_seconds=60):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            db_session_factory: callable returning a new sqlalchemy db session
            poll_seconds: number of seconds between db queries to detect
                chat requiring scheduling.
        """
        self.log = logging.getLogger(__name__)
        self.threadpool = NotificationThreadPool(num_threads, db_session_factory)
        self.db_queue = DatabaseJobQueue(
            owner='notificationsvc',
            model_class=NotificationJob,
            db_session_factory=db_session_factory,
            poll_seconds=poll_seconds,
        )

    def start(self):
        """Start the job monitor"""
        self.db_queue.start()
        while True:
            try:
                # delegate jobs to threadpool for processing
                self.threadpool.put(self.db_queue.get())
            except QueueStopped:
                break
            except Exception:
                pass
                # TODO? Okay to just fail. Think so.



