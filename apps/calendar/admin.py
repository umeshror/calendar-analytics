from django.contrib import admin

from models import Calendar, Event, Attendee, Account


class AttendeesInline(admin.TabularInline):
    """
    Show extra 3 rows of Attendee below Event Form
    """
    model = Attendee
    extra = 3


class EventAdmin(admin.ModelAdmin):
    search_fields = ['title', 'description']
    ordering = ['-start_time']
    list_display = ['title', 'start_time', 'end_time']
    inlines = (AttendeesInline,)


admin.site.register(Event, EventAdmin)


class CalendarAdmin(admin.ModelAdmin):
    search_fields = ['title', 'user']
    list_display = ['user', 'title', 'timezone']
    list_filter = ['user', 'title']


admin.site.register(Calendar, CalendarAdmin)


class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'email']
    list_filter = ['user', 'email']


admin.site.register(Account, AccountAdmin)


class AttendeeAdmin(admin.ModelAdmin):
    list_display = ['account', 'event', 'rsvp']
    list_filter = ['account', 'event', 'rsvp']


admin.site.register(Attendee, AttendeeAdmin)
