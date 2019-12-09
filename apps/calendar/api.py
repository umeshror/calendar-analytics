from datetime import datetime

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.utils.functional import cached_property

from apps.calendar.models import Calendar, Attendee


class CalendarAnalytics(object):
    def __init__(self, user, months=24, from_time=None, to_time=None):
        self.user = user
        self.calander = Calendar.objects.get(user=user)
        self.timezone = pytz.timezone(self.calander.timezone or 'UTC')
        self.to_datetime = to_time or datetime.today()
        self.from_datetime = from_time or self.to_datetime - relativedelta(months=months)

        self.events = self.calander.event_set.filter(
            start_time__gte=self.from_datetime
        )

    def max_meetings_with(self):
        """
        Returns list of people whom user had maximum meetings in given duration
        :return:
        """
        attendees = Attendee.objects.filter(event__in=self.events) \
            .values('account__email') \
            .exclude(account__email=self.user.email) \
            .annotate(count=Count('account__email')) \
            .order_by('-count')

        return [{'email': attendee["account__email"],
                 'count': attendee["count"]}
                for attendee in attendees]

    @cached_property
    def _events_df(self):
        data = self.events.values_list("id",
                                       "title",
                                       "start_time",
                                       "end_time")

        df = pd.DataFrame(data, columns=['id', 'title', 'start_time', 'end_time'])
        df['start_time'] = df['start_time'].dt.tz_convert(self.timezone)
        df['end_time'] = df['end_time'].dt.tz_convert(self.timezone)
        df["time_spent"] = df.apply(lambda row: self._get_duration(row['start_time'], row['end_time']), axis=1)
        return df

    def _get_duration(self, start_time, end_time):
        duration = end_time - start_time
        return int(duration.total_seconds())

    def _search_meetings(self, search_list):
        df = self._events_df
        df = df[df['title'].str.contains('|'.join(search_list))]
        return df

    def time_spent_on(self, search_list):
        df = self._search_meetings(search_list)
        return sum(df['time_spent'])

    def total_time_spent_by_month(self, from_time=None, to_time=None):
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%B'))['time_spent'].sum()
        return df.to_dict()

    def total_time_spent_by_week(self, from_time=None, to_time=None):
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].sum()
        return df.to_dict()

    def avg_time_spent_by_week(self, from_time=None, to_time=None):
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].mean()
        return df.to_dict()

    def avg_meetings_by_week(self, from_time=None, to_time=None):
        df = self._filter_df_by_duration(from_time, to_time)
        df = df.groupby(df['start_time'].dt.strftime('%W'))['time_spent'].agg('count')
        return df.to_dict()

    def _filter_df_by_duration(self, from_time, to_time):
        df = self._events_df
        if from_time:
            df = df[df['start_time'] > from_time]
        if to_time:
            df = df[df['start_time'] < to_time]
        return df
