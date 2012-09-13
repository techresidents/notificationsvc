namespace java com.techresidents.services.notificationsvc.gen
namespace py trnotificationsvc.gen

include "core.thrift"


/* Exceptions */

exception UnavailableException {
    1: string fault,
}

exception InvalidNotificationException {
    1: string fault,
}



/* Notification Priority */
enum NotificationPriority {
    LOW_PRIORITY,
    DEFAULT_PRIORITY,
    HIGH_PRIORITY,
}


/* Notification */
struct Notification {
    1: optional string token,
    2: NotificationPriority priority,
    3: optional list<string> recipientEmails,
    4: optional list<string> recipientUserIds,
    5: string title,
    6: optional string htmlText,
    7: optional string plainText,
    8: double createdTimestamp,
}


service TNotificationService extends core.TRService
{
    Notification notify(
                1: string context,
                2: Notification notification) throws (
                        1:UnavailableException unavailableException,
                        2:InvalidNotificationException invalidNotificationException),

        void cancel(
                1: string token,
                2: string context) throws (
                        1:UnavailableException unavailableException,
                        2:InvalidNotificationException invalidNotificationException),
}
