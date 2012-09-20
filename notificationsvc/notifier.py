
import datetime
import logging

from sqlalchemy.sql import func

from trnotificationsvc.gen.ttypes import NotificationPriority, Notification
from trpycore.timezone import tz
from trsvcscore.db.models import NotificationJob
from trsvcscore.db.job import DatabaseJob, DatabaseJobQueue, JobOwned, QueueEmpty, QueueStopped

from providers.exceptions import InvalidParameterException

#TODO delete exception.py if not needed anymore


class Notifier(object):
    """ Responsible for sending notifications.

    Args:
        db_session_factory:
        email_provider:
        job_retry_seconds:
    """

    def __init__(
            self,
            db_session_factory,
            email_provider,
            job_retry_seconds
    ):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.email_provider = email_provider
        self.job_retry_seconds = job_retry_seconds

    def _retry_job(self, failed_job):
        """Create a new NotificationJob from a failed job.

        This method creates a new Notification Job from a
        job that failed to process successfully. The job
        is added to the db.
        """
        try:
            db_session = None

            #create new job in db to retry.
            if failed_job.retries_remaining > 0:
                not_before = tz.utcnow() + datetime.timedelta(seconds=self.job_retry_seconds)
                new_job = NotificationJob(
                    created=func.current_timestamp(),
                    not_before=not_before,
                    notification_id=failed_job.notification_id,
                    recipient_id=failed_job.recipient_id,
                    priority=failed_job.priority,
                    retries_remaining=failed_job.retries_remaining-1
                )
                # Add job to db
                db_session = self.db_session_factory()
                db_session.add(new_job)
                db_session.commit()
            else:
                self.log.info("No retries remaining for job for notification_job_id=%s"\
                              % (failed_job.id))
                self.log.error("Job for notification_job_id=%s failed!"\
                               % (failed_job.id))
        except Exception as e:
            self.log.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()


    def send(self, database_job):
        try:
            with database_job as job:

                # Claiming the job and finishing the job are
                # handled by this context manager. Here, we
                # specify how to process the job.

                # This is where the logic that controls which
                # provider to use will live (e.g. email, sms, etc).
                # For now, we only have an email provider so
                # there's no control logic.

                # Do any text substitution here
                # subject = self.template_engine.substitute([], job.notification.subject)
                # plain_text = self.template_engine.substitute([], job.notification.plainText)
                # html_text = self.template_engine.substitute([], job.notification.htmlText)

                # Call into email service wrapper
                # TODO return async object
                result = self.email_provider.send(
                    recipient=job.recipient.email,
                    subject=job.notification.subject,
                    plain_text=job.notification.plain_text,
                    html_text=job.notification.html_text
                    #job.notification.attachments,
                )

        except JobOwned:
            # This means that the NotificationJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
            self.log.warning("Notification job with job_id=%d already claimed. Stopping processing." % job.id)
            pass
        except InvalidParameterException as e:
            self.log.exception(e)
            self._retry_job(job)
        except Exception as e:
            #failure during processing.
            self.log.exception(e)
            self._retry_job(job)
