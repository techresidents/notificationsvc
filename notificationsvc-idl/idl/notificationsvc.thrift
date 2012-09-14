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


/*
Notification
   token: optional ID. Used to support cancel() functionality in the Notification Service.
   context: the request context
   priority: the notification priority
   recipientUserIds: list of recipient user IDs to receive this notification
   subject: notification subject
   htmlText: notification body in HTML
   plainText: notification body in plain text
*/
struct Notification {
    1: optional string token,
    2: NotificationPriority priority,
    3: list<string> recipientUserIds,
    4: string subject,
    5: optional string htmlText,
    6: optional string plainText,
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
