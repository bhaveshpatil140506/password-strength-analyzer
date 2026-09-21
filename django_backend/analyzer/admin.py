from django.contrib import admin

from .models import (AdminActivityLog, AnalyzedPassword, CommonPassword,
                     LoginAttempt, Recommendation, Report, User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'fullname', 'email', 'is_admin', 'is_active', 'last_login')
    search_fields = ('username', 'email', 'fullname')
    list_filter = ('is_admin', 'is_active')


@admin.register(AnalyzedPassword)
class AnalyzedPasswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'password_placeholder', 'user', 'strength_label',
                    'strength_score', 'is_common', 'breached_count', 'analyzed_at')
    search_fields = ('password_placeholder', 'user__username')


@admin.register(CommonPassword)
class CommonPasswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'password_plaintext', 'appearance_rank')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'severity', 'is_applied', 'created_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'report_type', 'total_analyses', 'avg_strength', 'generated_at')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'success', 'ip_address', 'attempted_at')


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'admin', 'action', 'target_user', 'created_at')