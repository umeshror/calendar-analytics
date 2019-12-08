import json
from urllib import urlencode
from urllib2 import Request, urlopen

from django.apps import apps
from django.conf import settings
from oauth2client import client

UserOauthToken = apps.get_model('authenticate', 'UserOauthToken')
Calendar = apps.get_model('calendar', 'Calendar')


def get_calendar_list(user, service):
    """
    Get All Calendars of User including secondary
    :param user: <User> Instance
    :param service: GoogleCredentials Service
    :return: [<List of Calendars>]
    """
    try:
        calendars = []
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            calendars.extend(calendar_list['items'])
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        return calendars
    except (client.AccessTokenRefreshError, client.FlowExchangeError, client.AccessTokenCredentialsError, ValueError):
        # The credentials have been revoked or expired, please re-run the application to re-authorize.
        user.useroauthtoken.access_token  = get_new_access_token(user.useroauthtoken)
        user.useroauthtoken.save()
        return get_calendar_list(user, service)


def get_new_access_token(refresh_token):
    """
    gets new Access Token when existing Access Token expires
    :param useroauthtoken: <USerOauthToken Instance
    :return: New access_token
    """
    request = Request('https://accounts.google.com/o/oauth2/token',
                      data=urlencode({
                          'grant_type': 'refresh_token',
                          'client_id': settings.CALENDAR_CLIENT_ID,
                          'client_secret': settings.CALENDAR_CLIENT_SECRET,
                          'refresh_token': refresh_token
                      }),
                      headers={
                          'Content-Type': 'application/x-www-form-urlencoded',
                          'Accept': 'application/json'
                      }
                      )
    response = json.load(urlopen(request))
    return response['access_token']
