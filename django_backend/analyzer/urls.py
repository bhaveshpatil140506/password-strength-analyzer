from django.urls import path

from . import views

urlpatterns = [
    path('register', views.api_register, name='api-register'),
    path('login', views.api_login, name='api-login'),
    path('analyze', views.api_analyze, name='api-analyze'),
    path('common-check', views.api_common_check, name='api-common-check'),
    path('history', views.api_history, name='api-history'),
    path('report', views.api_report, name='api-report'),
    path('admin', views.api_admin, name='api-admin'),
]