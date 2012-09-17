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
    DEFAULT_PRIORITY,
    LOW_PRIORITY,
    HIGH_PRIORITY,
}


/*
Notification
   token: optional ID. Used to support cancel() functionality in the Notification Service.
   notBefore: the time to begin processing the notification (epoch timestamp)
   context: the request context
   priority: the notification priority
   recipientUserIds: list of recipient user IDs to receive this notification
   subject: notification subject
   htmlText: notification body in HTML
   plainText: notification body in plain text
*/
struct Notification {
    1: optional string token,
    2: optional double notBefore,
    3: NotificationPriority priority,
    4: list<i32> recipientUserIds,
    5: string subject,
    6: optional string htmlText,
    7: optional string plainText,
}


service TNotificationService extends core.TRService
{
    /*
        Send a notification.
        Args:
            context: string representing the request context
            notification: notification object
        Returns:
            The notification object. If no token attribute is
            provided in the input notification object, the
            returned object will specify one.
    */
    Notification notify(
        1: string context,
        2: Notification notification) throws (
                1:UnavailableException unavailableException,
                2:InvalidNotificationException invalidNotificationException),

    /*
    For future.
    void cancel(
        1: string token,
        2: string context) throws (
                1:UnavailableException unavailableException,
                2:InvalidNotificationException invalidNotificationException),
    */
}
