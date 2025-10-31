from django.urls import path

from .views import request_captcha, verify_captcha
from .views_admin import AdminCaptchaTypeView

urlpatterns = [
    path('captcha/request', request_captcha, name='captcha_request'),
    path('captcha/verify', verify_captcha, name='captcha_verify'),
    path('admin/captcha_types', AdminCaptchaTypeView.as_view(), name='admin_captcha_types'),
]
