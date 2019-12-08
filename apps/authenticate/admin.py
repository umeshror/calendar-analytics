from django.contrib import admin

from models import UserOauthToken


class UserOauthTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'access_token', 'token_expiry']
    list_filter = ['user']


admin.site.register(UserOauthToken, UserOauthTokenAdmin)
