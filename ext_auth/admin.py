from django.contrib import admin
from .models import ExternalUserIdentifier
# Register your models here.

class ExternalUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uid', 'platform')
    list_display_links = ('id',)
    list_filter = ('platform',)
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name', 
        'user__email',
        'uid',]


admin.site.register(ExternalUserIdentifier, ExternalUserAdmin)
