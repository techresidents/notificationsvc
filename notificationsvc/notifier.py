
import datetime
import logging
from string import Template

from sqlalchemy.sql import func

from trpycore.timezone import tz
from trsvcscore.db.models import NotificationJob
from trsvcscore.db.job import JobOwned




class Notifier(object):
    """ Responsible for sending notifications.

    Args:
        db_session_factory: callable returning a new sqlalchemy db session
        email_provider: Concrete object derived from EmailProvider
        job_retry_seconds: number of seconds delay between job retries
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
        job that failed to process successfully.
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


    def _substitute(self, templatized_string, template_dict):
        """Substitute dynamic values for placeholder text.

        The template.substitute() method can raise a ValuesError
        exception if no value exists in the provided template_dict
        for the template string. The notification service interface
        (the notify method) currently validates the template
        strings before continuing processing, so this should
        never raise an exception from here.

        Args:
            templatized_string: template String. Uses string.Template
            template_dict: template values
        Returns:
            String with substituted values
        """
        template = Template(templatized_string)
        return template.substitute(template_dict)


    def send(self, database_job):
        """ Send the notification specified by the input job.

        Args:
            database_job: DatabaseJob object, or objected derived from DatabaseJob
        """
        try:
            with database_job as job:

                # Claiming the job and finishing the job are
                # handled by this context manager. Here, we
                # specify how to process the job. The context
                # manager returns 'job' as a NotificationJob
                # db model object.

                # This is where the logic that controls which
                # provider to use will live (e.g. email, sms, etc).
                # For now, we only have an email provider so
                # there's no logic needed.

                # Fill in template values, if provided
                template_dict = {
                    'first_name': job.recipient.first_name,
                    'last_name': job.recipient.last_name}
                subject = self._substitute(job.notification.subject, template_dict)
                plain_text = self._substitute(job.notification.plain_text, template_dict)
                html_text = self._substitute(job.notification.html_text, template_dict)

                # Call into email service wrapper
                # TODO return async object
                result = self.email_provider.send(
                    recipient=job.recipient.email,
                    subject=subject,
                    plain_text=plain_text,
                    html_text=html_text
                    #job.notification.attachments in future
                )

        except JobOwned:
            # This means that the NotificationJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
            self.log.warning("Notification job with job_id=%d already claimed. Stopping processing." % job.id)
        except Exception as e:
            #failure during processing.
            self.log.exception(e)
            self._retry_job(job)
