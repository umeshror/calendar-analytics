from __future__ import absolute_import

from datetime import datetime

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.utils.functional import cached_property
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calendar.models import Calendar, Attendee


class AnalyticsAPIView(APIView):
    """
    Analytics API gives insights of User's meetings
    """

    def get(self, request):
        user = request.user

        ca = CalendarAnalytics(user)

        data = {}
        dt_3_months = datetime.now(tz=pytz.timezone('Asia/Kolkata')) - relativedelta(months=3)
        dt_12_months = datetime.now(tz=pytz.timezone('Asia/Kolkata')) - relativedelta(months=12)

        stats_12_months = ca.total_time_spent_by_month(from_time=dt_12_months)
        data["month"] = {
            "busy": max(stats_12_months, key=stats_12_months.get),
            "relax": min(stats_12_months, key=stats_12_months.get),
            "last_3_months": ca.total_time_spent_by_month(from_time=dt_3_months),
        }

        stats_52_weeks = ca.total_time_spent_by_month(from_time=dt_12_months)
        data["week"] = {
            "busy": max(stats_52_weeks, key=stats_52_weeks.get),
            "relax": min(stats_52_weeks, key=stats_52_weeks.get),
            "avg_time": ca.avg_time_spent_by_week(from_time=dt_12_months),
            "meetings_cnt": ca.avg_meetings_by_week(from_time=dt_12_months),
        }

        data['top_attendee'] = ca.max_meetings_with()[:3]

        data["time_spent"] = {
            'recruit': ca.time_spent_on(['Recruitment', 'Interview', 'Resume']),
            'standup': ca.time_spent_on(['standup', 'Stand up', 'catch up']),
            'zoom': ca.time_spent_on(['Zoom call']),
        }
        return Response(data)


class CalendarAnalytics(object):
    """
    Uses user's Calendar and its fetches events for
    analytical purpose
    """

    def __init__(self, user, months=24, from_time=None, to_time=None):
        self.user = user
        self.calander = Calendar.objects.get(user=user)
        self.timezone = pytz.timezone(self.calander.timezone or 'UTC')
        # from_datetime to to_datetime used to fetch events in specific duration
        to_datetime = to_time or datetime.today()
        from_datetime = from_time or to_datetime - relativedelta(months=months)

        self.events = self.calander.event_set.filter(
            start_time__gte=from_datetime
        )

    def max_meetings_with(self):
        """
        Returns list of people whom user had attended maximum meetings
        :return: [{email: "a@a.com", count: 23}]
        """
        attendees = Attendee.objects.filter(event__in=self.events) \
            .values('account__email') \
            .exclude(account__email=self.user.email) \
            .annotate(count=Count('account__email')) \
            .order_by('-count')

        return [{'email': attendee["account__email"],
                 'count': attendee["count"]}
                for attendee in attendees]

    # used cached_property to reused this df again and again
    @cached_property
    def _events_df(self):
        """
        Converts instance's events to DataFrame
        :return:
        id  title  start_time  end_time     time_spent
        1    xx    timsestamp  timsestamp   in seconds
        """
        data = self.events.values_list("id",
                                       "title",
                                       "start_time",
                                       "end_time")

        df = pd.DataFrame(data, columns=['id', 'title', 'start_time', 'end_time'])
        # Convert start_time and start_time and end_time to  calander's timezone
        df['start_time'] = df['start_time'].dt.tz_convert(self.timezone)
        df['end_time'] = df['end_time'].dt.tz_convert(self.timezone)
        # add new column 'time_spent' which stores time duration of meeting
        df["time_spent"] = df.apply(lambda row: self._get_duration(row['start_time'], row['end_time']), axis=1)
        return df

    def _get_duration(self, start_time, end_time):
        """
        Gets start_time and end_time, and returns
        time duration in 'SECONDS'
        :param start_time: <TimeStamp obj>
        :param end_time: <TimeStamp obj>
        :return: 123123 in Seconds
        """
        duration = end_time - start_time
        return int(duration.total_seconds())

    def _search_meetings(self, search_list):
        """
        Search all meetings for letters provided
        :param search_list: ['str1', 'str2']
        :return: Return DataFrame
        """
        df = self._events_df
        df = df[df['title'].str.contains('|'.join(search_list))]
        return df

    def time_spent_on(self, search_list):
        """
        Searches meeting for given Strings/Topics and
        returns total time spent of it in SECONDS
        :param search_list:
        :return:
        """
        df = self._search_meetings(search_list)
        return sum(df['time_spent'])

    def total_time_spent_by_month(self, from_time=None, to_time=None):
        """
        Returns Total time spent by MONTH for provided
        'from_time' and 'to_time'
        :param from_time: <DateTime obj>
        :param to_time: <DateTime obj>
        :return:{'month_name': time_spent_in_seconds,
                    'January': 261000}
        """
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%B'))['time_spent'].sum()
        return df.to_dict()

    def total_time_spent_by_week(self, from_time=None, to_time=None):
        """
        Returns Total time spent by WEEK for provided
        'from_time' and 'to_time'
        :param from_time: <DateTime obj>
        :param to_time: <DateTime obj>
        :return:{'week_number': time_spent_in_seconds,
                 '01': 261000}
        """
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].sum()
        return df.to_dict()

    def avg_time_spent_by_week(self, from_time=None, to_time=None):
        """
        Returns AVERAGE time spent by WEEK for provided
        'from_time' and 'to_time'
        :param from_time: <DateTime obj>
        :param to_time: <DateTime obj>
        :return:{'week_number': avg_spent_in_seconds,
                 '01': 3600}
        """
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].mean()
        return df.to_dict()

    def avg_meetings_by_week(self, from_time=None, to_time=None):
        """
        Returns AVERAGE meetings by WEEK for provided
        'from_time' and 'to_time'
        :param from_time: <DateTime obj>
        :param to_time: <DateTime obj>
        :return:{'week_number': number_of_meetings,
                 '01': 12}
        """
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].agg('count')
        return df.to_dict()

    def _filter_df_by_duration(self, from_time, to_time):
        """
        Filters DataFrame for from_time to to_time
        :param from_time: <DateTime obj>
        :param to_time: <DateTime obj>
        :return: <DataFrame obj>
        """
        df = self._events_df
        if from_time:
            df = df[df['start_time'] > from_time]
        if to_time:
            df = df[df['start_time'] < to_time]
        return df
