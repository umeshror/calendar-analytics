from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt

from apps.authenticate.views import OAuth, OAuth2CallBack
from apps.calendar.api import AnalyticsAPIView
from apps.calendar.views import FetchEventView
from apps.views import index

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth-login/$', csrf_exempt(OAuth.as_view()), name='oauth'),
    url(r'^oauth-callback/$', OAuth2CallBack.as_view(), name='oauth2_callback'),
    url(r'^fetch-events/$', FetchEventView.as_view(), name='fetch_events'),
    url(r'^analytics/$', AnalyticsAPIView.as_view(), name='analytics'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
