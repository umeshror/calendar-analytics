import mock as mock
import pandas as pd
from django.contrib.auth.models import User
from django.test import TestCase
from pandas._libs.tslibs.timestamps import Timestamp

from apps.calendar.api import CalendarAnalytics
from apps.calendar.models import Calendar, Event
from apps.calendar.views import get_or_create_events, get_or_create_calendar, get_organiser, get_utc_time, \
    create_attendees


class TestEventCreation(TestCase):
    EVENTS_DATA = [
        {
            "end": {
                "dateTime": "2015-06-24T15:30:00+05:30"
            },
            "description": "descicption1",
            "created": "2015-06-19T16:20:45.000Z",
            "htmlLink": "www.example.com/1",
            "updated": "2015-06-24T04:31:45.434Z",
            "summary": "One on one ",
            "start": {
                "dateTime": "2015-06-24T14:30:00+05:30"
            },
            "location": "Skype",
            "attendees": [
                {
                    "self": True,
                    "email": "admin@admin.com",
                    "responseStatus": "accepted"
                },
                {
                    "organizer": True,
                    "displayName": "Giles Barker",
                    "email": "user@admin.com",
                    "responseStatus": "accepted"
                }
            ],
            "organizer": {
                "email": "user@admin.com"
            },
            "creator": {
                "email": "admin@admin.com"
            },
            "id": "752jkq80k2213ed13e13134"
        },
        {
            "end": {
                "timeZone": "Asia/Kolkata",
                "dateTime": "2015-08-03T10:15:00+05:30"
            },
            "created": "2015-08-03T04:04:32.000Z",
            "htmlLink": "www.example.com/2",
            "updated": "2015-08-03T08:25:01.102Z",
            "summary": "Standup Meeting",
            "start": {
                "timeZone": "Asia/Kolkata",
                "dateTime": "2015-08-03T10:00:00+05:30"
            },
            "attendees": [
                {
                    "email": "admin@admin.com",
                    "responseStatus": "declined"
                },
                {
                    "email": "admin2@admin.com",
                    "responseStatus": "needsAction"
                },
                {
                    "email": "user2@admin.com",
                    "responseStatus": "accepted"
                }
            ],
            "organizer": {
                "email": "admin@group.calendar.google.com"
            },
            "creator": {
                "email": "admin2@admin.com"
            },
            "id": "752jkq80k2213ed13jgpo"
        }]

    def setUp(self):
        self.user = User.objects.create(username='admin',
                                        email='admin@admin.com')

        self.calendar = Calendar.objects.create(user=self.user,
                                                cal_id=self.user.email,
                                                title=self.user.email,
                                                timezone='Asia/Kolkata',
                                                events_sync_token="events_sync_token")

    def test_get_or_create_calendar(self):
        actual_output = get_or_create_calendar(self.user, {
            "id": "admin@example.com",
            "title": "title@example.com",
            "timezone": "Asia/Kolkata"
        })
        self.assertEquals(actual_output.cal_id, "admin@example.com")
        self.assertEquals(actual_output.title, "title@example.com")
        self.assertEquals(actual_output.timezone, "Asia/Kolkata")

    def test_get_organiser(self):
        record = {
            "organizer": {
                "email": "user@admin.com"
            },
            "creator": {
                "email": "admin2@admin.com"
            }
        }
        actual_output = get_organiser(record)
        self.assertEquals(actual_output.email, "user@admin.com")

        record = {
            "organizer": {
            },
            "creator": {
                "email": "admin2@admin.com"
            }
        }
        actual_output = get_organiser(record)
        self.assertEquals(actual_output.email, "admin2@admin.com")

    def test_get_utc_time(self):
        dt = get_utc_time("2015-08-03T10:15:00+05:30", "Asia/Kolkata")
        self.assertEquals(dt.isoformat(), '2015-08-03T10:15:00+05:30')

        dt = get_utc_time("2015-08-03", "Asia/Kolkata", is_date=True)
        self.assertEquals(dt.isoformat(), '2015-08-03T00:00:00+05:30')

    def test_get_or_create_events(self):
        actual_output = get_or_create_events(self.calendar, self.EVENTS_DATA)
        self.assertEquals(len(actual_output), 2)
        event1 = actual_output[0]
        self.assertEquals(event1.location, self.EVENTS_DATA[0]["location"])
        self.assertEquals(event1.event_link, self.EVENTS_DATA[0]["htmlLink"])
        self.assertEquals(event1.title, self.EVENTS_DATA[0]["summary"])
        self.assertEquals(event1.id, self.EVENTS_DATA[0]["id"])

    def test_create_attendees(self):
        event = Event.objects.create(
            id=self.EVENTS_DATA[0]["id"],
            location=self.EVENTS_DATA[0]["location"],
            event_link=self.EVENTS_DATA[0]["htmlLink"],
            title=self.EVENTS_DATA[0]["summary"],
            description=self.EVENTS_DATA[0]["description"],
            created_at=get_utc_time("2015-08-05T10:15:00+05:30", "Asia/Kolkata"),
            start_time=get_utc_time("2015-08-03T10:15:00+05:30", "Asia/Kolkata"),
            end_time=get_utc_time("2015-08-03T11:15:00+05:30", "Asia/Kolkata"),
        )
        attendees_records = [
            {
                "email": "admin@admin.com",
                "responseStatus": "declined"
            },
            {
                "email": "admin2@admin.com",
                "responseStatus": "needsAction"
            },
            {
                "email": "user2@admin.com",
                "responseStatus": "accepted"
            }
        ]
        actual_output = create_attendees(event, attendees_records)
        self.assertEquals(len(actual_output), 3)
        actual_emails = [attendee.account.email for attendee in actual_output]
        expected_emails = ["admin@admin.com", "admin2@admin.com", "user2@admin.com"]
        self.assertCountEqual(actual_emails, expected_emails)
        self.assertEquals(actual_output[0].event, event)


class TestCalendarAnalytics(TestCase):
    DATA = {'end_time': {0: Timestamp('2019-03-15 13:00:00+0530', tz='Asia/Kolkata'),
                         1: Timestamp('2019-06-21 14:30:00+0530', tz='Asia/Kolkata'),
                         2: Timestamp('2019-02-26 17:30:00+0530', tz='Asia/Kolkata'),
                         3: Timestamp('2019-06-12 18:15:00+0530', tz='Asia/Kolkata'),
                         4: Timestamp('2019-01-11 11:00:00+0530', tz='Asia/Kolkata')},
            'id': {0: 'sdacdcasd23vasdvasdvas',
                   1: 'sdacdca223sdvasdvasdvas',
                   2: 'sdacdcas233dvasdvasdvas',
                   3: 'sdac2dca2sdvasdvasdvas',
                   4: 'sda3cdcasdvasdvasdvas'},
            'start_time': {0: Timestamp('2019-03-15 12:00:00+0530', tz='Asia/Kolkata'),
                           1: Timestamp('2019-06-21 14:00:00+0530', tz='Asia/Kolkata'),
                           2: Timestamp('2019-02-26 16:30:00+0530', tz='Asia/Kolkata'),
                           3: Timestamp('2019-06-12 17:00:00+0530', tz='Asia/Kolkata'),
                           4: Timestamp('2019-01-11 10:00:00+0530', tz='Asia/Kolkata')},
            'time_spent': {0: 3600, 1: 1800, 2: 3600, 3: 4500, 4: 3600},
            'title': {0: 'CV review-Senior Full Stack Developer',
                      1: 'Grower onboarding | show and tell ',
                      2: 'Assignment Review',
                      3: 'Interview (Lead Mobile Developer)',
                      4: 'Standup catchcup'}}

    def setUp(self):
        self.user = User.objects.create(username='admin',
                                        email='admin@admin.com')

        self.calendar = Calendar.objects.create(user=self.user,
                                                cal_id=self.user.email,
                                                title=self.user.email,
                                                timezone='Asia/Kolkata',
                                                events_sync_token="events_sync_token")

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test__search_meetings(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca._search_meetings(['Standup']).to_dict()

        expected_output = {'end_time': {4: Timestamp('2019-01-11 10:00:00+0530', tz='Asia/Kolkata')},
                           'id': {4: 'sda3cdcasdvasdvasdvas'},
                           'start_time': {4: Timestamp('2019-01-11 10:00:00+0530', tz='Asia/Kolkata')},
                           'time_spent': {4: 3600},
                           'title': {4: 'Standup catchcup'}}

        self.assertDictEqual(actual_output, expected_output)

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test_time_spent_on(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca.time_spent_on(['Standup']).to_dict()
        expected_output = 3600
        self.assertEqual(actual_output, expected_output)

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test_total_time_spent_by_month(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca.total_time_spent_by_month()
        expected_output = {'February': 3600, 'January': 3600, 'June': 6300, 'March': 3600}
        self.assertEqual(actual_output, expected_output)

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test_total_time_spent_by_week(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca.total_time_spent_by_week()
        expected_output =  {'01': 3600, '08': 3600, '10': 3600, '23': 4500, '24': 1800}
        self.assertEqual(actual_output, expected_output)

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test_avg_time_spent_by_week(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca.avg_time_spent_by_week()
        expected_output = {'01': 3600, '08': 3600, '10': 3600, '23': 4500, '24': 1800}
        self.assertEqual(actual_output, expected_output)

    @mock.patch.object(CalendarAnalytics, "_events_df")
    def test_avg_meetings_by_week(self, _events_df):
        _events_df.return_value = pd.DataFrame(self.DATA)
        ca = CalendarAnalytics(self.user)
        actual_output = ca.avg_meetings_by_week()
        expected_output = {'01': 1, '08': 1, '10': 1, '23': 1, '24': 1}
        self.assertEqual(actual_output, expected_output)
