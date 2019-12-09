from __future__ import absolute_import

import pytz
from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import View
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from apps.authenticate.models import UserOauthToken
from apps.calendar.models import Event, Attendee, Account, Calendar
from apps.calendar.utils import get_new_access_token


class FetchEventView(View):
    """
    Redirected when user gives consent to access calendar data and
    system gets AccessToken and RefreshToken
    With help og these AccessToken and RefreshToken we can do further
    queries to Google Calendar

    """

    def get(self, request, *args, **kwargs):
        user_oauth = UserOauthToken.objects.get(user=request.user)
        if user_oauth.is_token_expired():
            user_oauth.access_token = get_new_access_token(user_oauth.refresh_token)
            user_oauth.save()

        credentials = Credentials(
            token=user_oauth.access_token,
            refresh_token=user_oauth.refresh_token,
            client_id=settings.CALENDAR_CLIENT_ID,
            token_uri=settings.CALENDAR_OAUTH_REDIRECT_URI,
            client_secret=settings.CALENDAR_CLIENT_SECRET,
            scopes=settings.CALENDAR_SCOPE
        )
        service = build("calendar", "v3", credentials=credentials)
        calendar_record = service.calendars().get(calendarId='primary').execute()

        calendar = get_or_create_calendar(user_oauth.user, calendar_record)
        # sync_token will make sure we are not fetching same events again anad again
        sync_token = calendar.events_sync_token or None
        events = []
        page_token = None
        while True:
            response = service.events().list(calendarId='primary',
                                             pageToken=page_token,
                                             syncToken=sync_token).execute()
            events.extend(response['items'])
            page_token = response.get('nextPageToken')
            if not page_token:
                # store the nextSyncToken in calendar as it belongs to calendar only
                calendar.events_sync_token = response.get("nextSyncToken")
                calendar.save()
                break

        events = get_or_create_events(calendar, events)

        return HttpResponseRedirect(reverse('index'))


def get_or_create_events(calendar, events):
    """
    Crates a unique event from Google Event ID
    This event then linked to calendar
    :param calendar: <calendar> instance
    :param events: List of Event dicts from Google API
    :return:
    """
    data = []
    with transaction.atomic():
        for record in events:
            if record['status'] == 'cancelled':
                return
            try:
                event = Event.objects.get(id=record['id'])
            except Event.DoesNotExist:

                organiser = get_organiser(record)

                event = Event(id=record['id'])
                event.location = record.get('location', '')
                event.event_link = record['htmlLink']
                event.title = record.get('summary', '')
                event.description = record.get('description', '')
                event.organiser = organiser

                start = record.get('start')
                if start.get("dateTime"):
                    start_time = get_utc_time(record['start']['dateTime'], calendar.timezone)
                else:
                    start_time = get_utc_time(record['start']['date'], calendar.timezone, is_date=True)

                end = record.get('end')
                if end.get("dateTime"):
                    end_time = get_utc_time(record['end']["dateTime"], calendar.timezone)
                else:
                    end_time = get_utc_time(record['end']["date"], calendar.timezone, is_date=True)

                event.start_time = start_time
                event.end_time = end_time

                event.created_at = get_utc_time(record["created"], calendar.timezone)
                event.updated_at = get_utc_time(record["updated"], calendar.timezone)
                event.save()
                if record.get('attendees'):
                    create_attendees(event, record['attendees'])
            data.append(event)
            event.calendar.add(calendar)
    return data


def create_attendees(event, attendees_records):
    """
    Creates Attendee for a single Event
    :param event: <Event> Instance
    :param attendees_dict: [{'email': 'email', 'responseStatus': 'status'}]
    :return:
    """
    attendees = []
    for record in attendees_records:
        email = record.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        account, _ = Account.objects.get_or_create(email=email, user=user)
        attendee, _ = Attendee.objects.update_or_create(account=account,
                                                        event=event,
                                                        rsvp=record['responseStatus'])
        attendees.append(attendee)
    return attendees


def get_utc_time(timezone_aware_ts, time_zone, is_date=False):
    """
    Converts datetime str to UTC datetime obj
    :param timezone_aware_ts: String rep of datetime
    :param time_zone: Calander time_zone
    :param is_date: is timezone_aware_ts date ?
    :return: utc aware datetime
    """
    tz = pytz.timezone(time_zone)
    if is_date:
        return tz.localize(parser.parse(timezone_aware_ts))
    return parser.parse(timezone_aware_ts)


def get_organiser(record):
    """
    Returns if organiser is present in data
    else retruen creator
    :param record: {
     'organizer': {'email': 'unknownorganizer@calendar.google.com'},
                  'creator': {'displayName': 'First LAst',
                               'email': 'creator@gmail.com',
                               'self': True}
                    }
    :return:
    """
    if record.get("organizer"):
        email = record['organizer']['email']
        if email == "unknownorganizer@calendar.google.com":
            email = record['creator']['email']
    else:
        email = record['creator']['email']
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None
    organiser, _ = Account.objects.get_or_create(email=email, user=user)
    return organiser


def get_or_create_calendar(user, calendar_record):
    """
    Look if calendar  already exists for user
    If exists then update title and timezone which are dynamic
    If not then creat new one
    :param calendar_record:{'id': 'sarukumesh@gmail.com',
                             'summary': 'sarukumesh@gmail.com',
                             'timeZone': 'Asia/Calcutta'}
    :param request:
    :return:
    """
    # from apps.calendar.models import Calendar
    calendar, _ = Calendar.objects.update_or_create(user=user,
                                                    cal_id=calendar_record["id"],
                                                    defaults={
                                                        'title': calendar_record["summary"],
                                                        'timezone': calendar_record["timeZone"],
                                                    })

    return calendar
