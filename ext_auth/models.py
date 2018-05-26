from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
# from oauth2_provider.models import get_application_model
ET_PLATFORM = (
    ("firebase", "Firebase Auth"),
)

# Create your models here.
class ExternalUserIdentifier(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=ET_PLATFORM, default='firebase')
    uid = models.CharField(max_length=150, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'External User'
        verbose_name_plural = 'External Users'