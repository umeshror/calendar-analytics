import arrow
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rest_framework.response import Response
from rest_framework.views import APIView

UserOauthToken = apps.get_model('authenticate', 'UserOauthToken')
Calendar = apps.get_model('calendar', 'Calendar')
Event = apps.get_model('calendar', 'Event')
Attendee = apps.get_model('calendar', 'Attendee')
Account = apps.get_model('calendar', 'Account')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class FetchEventAPIView(APIView):
    """
    Redirected when user gives consent to access calendar data and
    system gets AccessToken and RefreshToken
    With help og these AccessToken and RefreshToken we can do further
    queries to Google Calendar

    """

    def get(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        user_oauth = UserOauthToken.objects.get(user=request.user)

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

        return Response({"message": "{} Events fetched".format(len(events))})


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
                    start_time = get_utc_time(record['start']['dateTime'])
                else:
                    start_time = get_utc_time(record['start']['date'], is_date=True)

                end = record.get('end')
                if end.get("dateTime"):
                    end_time = get_utc_time(record['end']["dateTime"])
                else:
                    end_time = get_utc_time(record['end']["date"], is_date=True)

                event.start_time = start_time
                event.end_time = end_time

                event.created_at = get_utc_time(record["created"])
                event.updated_at = get_utc_time(record["updated"])
                event.save()
                if record.get('attendees'):
                    create_attendees(event, record['attendees'])
            data.append(event)
            event.calendar.add(calendar)
    return data


def create_attendees(event, attendees_dict):
    """
    Creates Attendee for a single Event
    :param event:
    :param attendees_dict:
    :return:
    """
    accounts = []
    for record in attendees_dict:
        email = record.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        account, _ = Account.objects.get_or_create(email=email, user=user)
        attendee, _ = Attendee.objects.update_or_create(account=account,
                                                        event=event,
                                                        rsvp=record['responseStatus'])
        accounts.append(account)
    return accounts


def get_utc_time(timezone_aware_ts, is_date=False):
    """
    Converts datetime str to UTC datetime obj
    :param timezone_aware_ts: String rep of datetime
    :return: utc aware datetime
    """

    arrow_ts = arrow.get(timezone_aware_ts)
    if not is_date:
        arrow_ts = arrow_ts.utcnow()
    return arrow_ts.datetime


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
    try:
        calendar = Calendar.objects.get(user=user,
                                        cal_id=calendar_record["id"]
                                        )
    except Calendar.DoesNotExist:
        calendar, created = Calendar.objects.create(user=user,
                                                    cal_id=calendar_record["id"],
                                                    title=calendar_record["summary"],
                                                    timezone=calendar_record["timeZone"]
                                                    )
    else:
        calendar.title = calendar_record["summary"]
        calendar.timezone = calendar_record["timeZone"]
        calendar.save()
    return calendar
