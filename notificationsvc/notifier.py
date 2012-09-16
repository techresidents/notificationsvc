
import logging

from sqlalchemy.sql import func

from trnotificationsvc.gen.ttypes import NotificationPriority, Notification
from trpycore.timezone import tz
from trsvcscore.db.models import Notification

from exceptions import DuplicateJobException



class Notifier(object):
    """ Responsible for sending notifications.
    """

    def __init__(self, db_session_factory, job_id):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.job_id = job_id

    def create_db_session(self):
        """Create  new sqlalchemy db session.

        Returns:
            sqlalchemy db session
        """
        return self.db_session_factory()

    def notify(self):
        """ Send notification.
        """
        try:
            pass
            #self._start_chat_persist_job()
            self._notify()
            #self._end_chat_persist_job()

        except DuplicateJobException as warning:
            self.log.warning("Notification job with job_id=%d already claimed. Stopping processing." % self.job_id)
            # This means that the NotificationJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.

        except Exception as e:
            #self._abort_chat_persist_job()
            pass


    def _notify(self):
        pass
        # Read notification based upon job_id
        # Call into email service wrapper
        # return async object