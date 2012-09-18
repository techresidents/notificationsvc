
import logging
import threading

from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.db.models import NotificationJob
from trsvcscore.db.job import DatabaseJob, DatabaseJobQueue, JobOwned, QueueEmpty, QueueStopped



class NotificationThreadPool(ThreadPool):
    """Thread pool used to process notifications.

    Given a work item (job_id), this class will process the
    job and delegate the work to send a notification.
    """
    def __init__(self, num_threads, db_session_factory, notifier_pool):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            db_session_factory: callable returning new sqlalchemy
                db session.
            notifier_pool: pool of Notifier objects responsible for
                sending notifications
        """
        super(NotificationThreadPool, self).__init__(num_threads)
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.notifier_pool = notifier_pool


    def process(self, database_job):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (job) is put on the queue.

        Args:
            database_job: DatabaseJob object, or objected derived from DatabaseJob
        """
        try:
            print '******************'
            print 'processing job....'
            print '******************'
            with self.notifier_pool.get() as notifier:
                notifier.send(database_job)

        except Exception as e:
            self.log.exception(e)



class NotificationJobMonitor(object):
    """
    NotificationJobMonitor monitors for new notification jobs, and delegates
     work items to a thread pool.
    """
    def __init__(self, db_session_factory, thread_pool, poll_seconds=60):
        """Constructor.

        Arguments:
            db_session_factory: callable returning a new sqlalchemy db session
            thread_pool: pool of worker threads
            poll_seconds: number of seconds between db queries to detect
                new jobs.
        """
        self.log = logging.getLogger(__name__)
        self.thread_pool = thread_pool
        self.poll_seconds = poll_seconds

        self.db_job_queue = DatabaseJobQueue(
            owner='notificationsvc',
            model_class=NotificationJob,
            db_session_factory=db_session_factory,
            poll_seconds=poll_seconds,
        )

        self.monitor_thread = threading.Thread(target=self.run)
        self.running = False


    def start(self):
        """Start job monitor."""
        if not self.running:
            self.running = True
            self.db_job_queue.start()
            self.monitor_thread.start()


    def run(self):
        """Monitor thread run method."""
        while self.running:
            try:
                self.log.info("NotificationJobMonitor is checking for new jobs to process...")

                # delegate jobs to threadpool for processing
                job = self.db_job_queue.get()
                self.thread_pool.put(job)

            except QueueEmpty:
                #TODO what to do here?
                pass
            except QueueStopped:
                break
            except Exception as error:
                self.log.exception(error)

        # TODO what to do when we break?
        self.running = False


    def stop(self):
        """Stop monitor."""
        if self.running:
            self.running = False
            self.db_job_queue.stop()


    def join(self, timeout):
        """Join all threads."""
        threads = [self.db_job_queue]
        if self.monitor_thread is not None:
            threads.append(self.monitor_thread)
        join(threads, timeout)
