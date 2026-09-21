"""Root URL configuration for the Password Strength Analyzer."""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from analyzer import views

urlpatterns = [
    # ---------- Django admin ----------
    path('django-admin/', admin.site.urls),

    # ---------- Frontend HTML pages ----------
    path('', RedirectView.as_view(url='/index.html', permanent=False)),
    path('index.html', views.page_index, name='page-index'),
    path('favicon.ico', RedirectView.as_view(url='/images/logo.svg', permanent=False)),
    path('login.html', views.page_login, name='page-login'),
    path('register.html', views.page_register, name='page-register'),
    path('analyzer.html', views.page_analyzer, name='page-analyzer'),
    path('dashboard.html', views.page_dashboard, name='page-dashboard'),
    path('history.html', views.page_history, name='page-history'),
    path('recommendations.html', views.page_recommendations, name='page-recommendations'),
    path('report.html', views.page_report, name='page-report'),
    path('admin_dashboard.html', views.page_admin, name='page-admin'),

    # ---------- Static css / js / images ----------
    path('css/<path:filename>', views.page_static, {'kind': 'css'}, name='static-css'),
    path('js/<path:filename>', views.page_static, {'kind': 'js'}, name='static-js'),
    path('images/<path:filename>', views.page_static, {'kind': 'images'}, name='static-images'),

    # ---------- REST API ----------
    path('api/', include('analyzer.urls')),
]