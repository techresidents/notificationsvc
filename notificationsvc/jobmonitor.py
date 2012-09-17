
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
        self.poll_seconds = poll_seconds
        self.threadpool = NotificationThreadPool(num_threads, db_session_factory)
        self.db_job_queue = DatabaseJobQueue(
            owner='notificationsvc',
            model_class=NotificationJob,
            db_session_factory=db_session_factory,
            poll_seconds=poll_seconds,
        )

        self.monitorThread = threading.Thread(target=self.run)
        self.exit = threading.Condition() #conditional variable allowing speedy wakeup on exit.
        self.running = False

    def start(self):
        """Start job monitor."""
        if not self.running:
            self.running = True
            self.threadpool.start()
            self.monitorThread.start()
            self.db_job_queue.start()


    def run(self):
        """Monitor thread run method."""
        while self.running:
            try:
                self.log.info("NotificationJobMonitor is checking for new jobs to process...")

                # delegate jobs to threadpool for processing
                self.threadpool.put(self.db_job_queue.get())

            except QueueEmpty:
                #TODO what to do here?
                pass
            except QueueStopped:
                break
            except Exception as error:
                self.log.exception(error)

            #TODO don't think I need this anymore either
            # Acquire exit conditional variable
            # and call wait on this to sleep the
            # necessary time between db checks.
            # Waiting on a conditional variable,
            # allows the wait to be interrupted
            # when stop() is called.
            with self.exit:
                end = time.time() + self.poll_seconds
                # wait in loop, rechecking condition to combat spurious wakeups.
                while self.running and (time.time() < end):
                    remaining_wait = end - time.time()
                    self.exit.wait(remaining_wait)

    def stop(self):
        """Stop monitor."""
        if self.running:
            self.running = False
            #acquire conditional variable and wake up monitorThread run method.
            with self.exit:
                self.exit.notify_all()
            self.threadpool.stop()
            self.db_job_queue.stop()

    def join(self, timeout):
        """Join all threads."""
        # TODO see archive service for minor tweaks
        join([self.threadpool, self.db_job_queue, self.monitorThread], timeout)
