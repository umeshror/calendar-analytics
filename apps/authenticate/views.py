import json

import httplib2
from django.apps import apps
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic.base import View
from oauth2client.client import OAuth2WebServerFlow

UserOauthToken = apps.get_model('authenticate', 'UserOauthToken')
Calendar = apps.get_model('calendar', 'Calendar')


class OAuth(View):
    """
    OAuth used for authenticating User to Google API
    Looks if user has already given permission in UserOauthToken
    If User found then redirect to home page
    else redirects to Google Auth page
    """

    def get(self, request):
        try:
            UserOauthToken.objects.get(user=request.user)
            return HttpResponseRedirect(reverse('index'))
        except UserOauthToken.DoesNotExist:
            flow = OAuth2WebServerFlow(settings.CALENDAR_CLIENT_ID,
                                       settings.CALENDAR_CLIENT_SECRET,
                                       scope=settings.CALENDAR_SCOPE,
                                       redirect_uri=settings.CALENDAR_OAUTH_REDIRECT_URI)
            generated_url = flow.step1_get_authorize_url()
        return HttpResponseRedirect(generated_url)


class OAuth2CallBack(View):
    """
    Redirected when user gives consent to access calendar data
    so, requests Google for AccessToken and RefreshToken
    Which means we can get AccessToken and RefreshToken for further
    queries to Google Calendar
    http://127.0.0.1:8000/oauth-callback/?code=4/uAGqh2dFw9i8dK08SotrRaN6BhTwpAD
    """

    def get(self, request):
        code = request.GET.get('code', False)
        if not code:
            return JsonResponse(
                {'status': 'No access key received from Google or User has declined the permission!'})

        flow = OAuth2WebServerFlow(settings.CALENDAR_CLIENT_ID,
                                   settings.CALENDAR_CLIENT_SECRET,
                                   redirect_uri=settings.CALENDAR_OAUTH_REDIRECT_URI,
                                   scope=settings.CALENDAR_SCOPE)
        credentials = flow.step2_exchange(code)

        http = httplib2.Http()
        credentials.authorize(http)
        response_data = json.loads(credentials.to_json())
        user_oauth = UserOauthToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': response_data["access_token"],
                'refresh_token': response_data["refresh_token"],
                'token_expiry': response_data["token_expiry"]
            })

        return HttpResponseRedirect(reverse('index'))
