from oauth2client import client

UserOauthToken = apps.get_model('authenticate', 'UserOauthToken')
Calendar = apps.get_model('calendar', 'Calendar')


def get_calendar_list(service):
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
    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')



def get_access_token():
    pass
