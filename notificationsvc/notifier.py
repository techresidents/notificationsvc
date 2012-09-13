
import logging

from sqlalchemy.sql import func

from trchatsvc.gen.ttypes import Message
from trpycore.timezone import tz
from trsvcscore.db.models import ChatPersistJob, ChatMessage, ChatMessageFormatType

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
            #self._persist_data()
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

