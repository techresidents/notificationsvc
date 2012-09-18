

# This dict was created to map the Thrift
# NotificationPriority enums to values.  The values
# were not included in the Thrift interface to
# facilitate easier maintenance should these
# values have to change.

# These are the values that will be written
# to the database 'priority' column.

#TODO replace hard coded id's with dynamic enum.
NOTIFICATION_PRIORITY_VALUES = {
    "HIGH_PRIORITY": 10,
    "DEFAULT_PRIORITY": 50,
    "LOW_PRIORITY": 100
}
