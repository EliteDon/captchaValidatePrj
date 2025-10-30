from django.contrib import admin

from .models import CaptchaChallenge, CaptchaType


@admin.register(CaptchaType)
class CaptchaTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'is_default', 'enabled', 'updated_at')
    list_editable = ('is_default', 'enabled')


@admin.register(CaptchaChallenge)
class CaptchaChallengeAdmin(admin.ModelAdmin):
    list_display = ('token', 'type', 'client_ip', 'created_at', 'expires_at', 'validated')
    list_filter = ('type', 'validated')
    search_fields = ('token', 'client_ip')
