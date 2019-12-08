from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

NEEDS_ACTION = 'needsAction'
DECLINED = 'declined'
TENTATIVE = 'tentative'
ACCEPTED = 'accepted'

RSVP_CHOICES = (
    (NEEDS_ACTION, 'Needs Action'),
    (DECLINED, 'Declined'),
    (TENTATIVE, 'Tentative'),
    (ACCEPTED, 'Accepted')
)


class Calendar(models.Model):
    """
    Primary Calendars of User's
    "Calendar has many Events"
    """
    user = models.ForeignKey(User)

    cal_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Calender's ID"
    )

    title = models.CharField(max_length=500,
                             help_text="Title/Summary of the Calendar")

    timezone = models.CharField(max_length=100,
                                blank=False,
                                help_text="Default timezone of the Calendar i.e. for its events")

    events_sync_token = models.CharField(max_length=255,
                                         help_text="SyncToken of the events in Calendar "
                                                   "used to get any new events of the Calendar")

    class Meta:
        unique_together = ('user', 'cal_id')

    def __unicode__(self):
        return self.title


class Account(models.Model):
    """
    People who are attending event
    Event has M2M to Attendee
    "Account has many Events"
    """
    user = models.ForeignKey(User, null=True, blank=True,
                             help_text="Link to User if exists in system")

    email = models.EmailField(unique=True,
                              help_text='Email of the attendee')

    def __unicode__(self):
        return self.email


class Attendee(models.Model):
    """
    Attendee is M2M to Event as an Event can have many
    attendee
    """
    account = models.ForeignKey(Account,
                                blank=False,
                                help_text="Account of Attendee")
    event = models.ForeignKey('Event',
                              blank=False,
                              help_text="Event for which User is doing RSVP")
    rsvp = models.CharField(
        max_length=40,
        choices=RSVP_CHOICES,
        default=NEEDS_ACTION,
        help_text='RSVP of the Attendee'
    )
    def __unicode__(self):
        return self.account

    class Meta:
        unique_together = ('account', 'event')
        auto_created = True

class Event(models.Model):
    """
    Store Events

    e.g.
    A is creator
    "A" User can have 'a' event for which "B" and "C" are users
    "B" User can have same event for which "A" and "C" are users

    """
    # MySQL does not allow unique CharFields to have a max_length > 255.

    id = models.CharField(
        max_length=255,
        primary_key=True,
        help_text="Calender's Event ID"
    )

    calendar = models.ManyToManyField(Calendar,
                                      help_text="A event can be linked to many Calendars")

    attendees = models.ManyToManyField(
        Account,
        through="Attendee",
        related_name="attendees",
        help_text='People who are attending this event'
    )

    event_link = models.CharField(
        max_length=255,
        blank=False,
        help_text="Link of Google Calendar Event"
    )
    title = models.CharField(
        max_length=256,
        help_text='Event Title/Summary',
        blank=False
    )
    description = models.TextField(blank=True,
                                   help_text='Event details')
    location = models.TextField(blank=True,
                                help_text='Location of the event')
    organiser = models.ForeignKey(Account,
                                  help_text="Organiser's field, "
                                            "set to creator if creator is User"
                                  )
    start_time = models.DateTimeField(
        help_text='Start time of the event'
    )
    end_time = models.DateTimeField(
        help_text='End time of the event'
    )
    created_at = models.DateTimeField(
        help_text='Event creation time'
    )
    updated_at = models.DateTimeField(
        help_text='Time when event was last updated'
    )

    def __unicode__(self):
        return self.title

    def is_event_happened(self):
        """
        Return's if current token is expired or not
        """
        return datetime.now() < self.end_time
