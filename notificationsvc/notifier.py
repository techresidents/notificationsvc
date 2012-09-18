
import copy
import logging

from sqlalchemy.sql import func

from trnotificationsvc.gen.ttypes import NotificationPriority, Notification
from trpycore.timezone import tz
from trsvcscore.db.models import NotificationJob
from trsvcscore.db.job import DatabaseJob, DatabaseJobQueue, JobOwned, QueueEmpty, QueueStopped


#TODO delete exception.py if not needed anymore


class Notifier(object):
    """ Responsible for sending notifications.
    """

    def __init__(self, db_session_factory, email_provider):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.email_provider = email_provider

    def _create_new_job(self, failed_job):
        """Create a new NotificationJob from a failed job.

        This method creates a new Notification Job from a
        job that failed to process successfully. The job
        is added to the db.
        """
        try:
            #create new job in db to retry.
            if failed_job.retries_remaining > 0:
                new_job = copy.deepcopy(failed_job)
                new_job.created = func.current_timestamp()
                new_job.retries_remaining = failed_job.retries_remaining-1

                # Add job to db
                db_session = self.create_db_session()
                db_session.add(new_job)
                db_session.commit()
        except Exception as e:
            self.log.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()

    def _create_db_session(self):
        """Create  new sqlalchemy db session.

        Returns:
            sqlalchemy db session
        """
        return self.db_session_factory()

    def send(self, database_job):
        try:
            with database_job as job:

                # Claiming the job and finishing the job are
                # handled by this context manager. Here, we
                # specify how to process the job.

                # Call into email service wrapper
                self.email_provider.send(
                    [job.recipient.email],
                    job.notification.subject,
                    job.notification.plainText,
                    job.notification.htmlText
                )

                # return async object
                # TODO

        except JobOwned:
            # This means that the NotificationJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
            self.log.warning("Notification job with job_id=%d already claimed. Stopping processing." % job.id)
            pass
        except Exception:
            #failure during processing.
            self._create_new_job(job)
