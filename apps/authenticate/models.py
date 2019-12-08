from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class UserOauthToken(models.Model):
    """
    Stores User's Oauth2 details
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text='User for whom token is generated',
    )

    access_token = models.CharField(
        max_length=255,
        blank=False,
        help_text='Access Token of the user which is used to access the content'
    )

    refresh_token = models.CharField(
        max_length=255,
        blank=False,
        help_text='Refresh Token of the user used when Access Token expiers'
    )

    token_expiry = models.DateTimeField(
        help_text='Datetime when Access Token expires'
    )

    def __unicode__(self):
        return self.user.username

    def is_token_expired(self):
        """
        Return's if current token is expired or not
        """
        return datetime.now() < self.token_expiry
