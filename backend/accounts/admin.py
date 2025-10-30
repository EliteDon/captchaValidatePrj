from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LoginRecord, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("扩展信息", {"fields": ("ip_address",)}),)
    list_display = ('username', 'email', 'is_staff', 'is_active', 'ip_address', 'last_login')
    search_fields = ('username', 'email')


@admin.register(LoginRecord)
class LoginRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'success', 'captcha_type', 'message')
    list_filter = ('success', 'captcha_type')
    search_fields = ('user__username', 'ip_address')
