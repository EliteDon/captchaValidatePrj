from django.urls import path

from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('admin/login', views.admin_login, name='admin_login'),
    path('admin/login_records', views.admin_login_records, name='admin_login_records'),
]
