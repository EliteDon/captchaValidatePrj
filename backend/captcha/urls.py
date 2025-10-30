from django.urls import path

from .views import admin_captcha_types, request_captcha, verify_captcha

urlpatterns = [
    path('captcha/request', request_captcha, name='captcha_request'),
    path('captcha/verify', verify_captcha, name='captcha_verify'),
    path('admin/captcha_types', admin_captcha_types, name='admin_captcha_types'),
]
