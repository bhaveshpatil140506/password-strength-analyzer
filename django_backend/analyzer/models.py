"""
Password Strength Analyzer - Django ORM models.

Mirrors the phpMyAdmin / MySQL schema (database: password_analyzer).
NOTE: If you prefer the PHP backend to own the schema, run Django with
a SEPARATE database name to avoid table collisions. Both backends are
kept compatible here for demo purposes.
"""

from django.contrib.auth.hashers import make_password, check_password
from django.db import models


def hash_password(raw: str) -> str:
    """bcrypt (Django default for password-style hashes)."""
    return make_password(raw, hasher='pbkdf2_sha256')


class User(models.Model):
    class Meta:
        db_table = 'users'
        ordering = ['id']

    fullname = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=120, unique=True)
    password_hash = models.CharField(max_length=255)
    security_question = models.CharField(max_length=255, null=True, blank=True)
    security_answer_hash = models.CharField(max_length=255, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def verify_password(self, raw: str) -> bool:
        return check_password(raw, self.password_hash)

    def __str__(self):
        return f'<User {self.username}>'


class AnalyzedPassword(models.Model):
    class Meta:
        db_table = 'analyzed_passwords'
        ordering = ['-analyzed_at']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    password_placeholder = models.CharField(max_length=255)
    strength_score = models.IntegerField(default=0)
    strength_label = models.CharField(max_length=20, null=True, blank=True)
    length = models.IntegerField(default=0)
    has_uppercase = models.BooleanField(default=False)
    has_lowercase = models.BooleanField(default=False)
    has_numbers = models.BooleanField(default=False)
    has_special = models.BooleanField(default=False)
    character_count = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    link_speed = models.CharField(max_length=30, null=True, blank=True)
    estimated_crack_time = models.CharField(max_length=60, null=True, blank=True)
    is_common = models.BooleanField(default=False)
    breached_count = models.IntegerField(default=0)
    entropy = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    analysis_notes = models.TextField(null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'<Analysis #{self.pk} {self.password_placeholder}>'


class CommonPassword(models.Model):
    class Meta:
        db_table = 'common_passwords'

    password_hash = models.CharField(max_length=64, unique=True)
    password_plaintext = models.CharField(max_length=255, null=True, blank=True)
    appearance_rank = models.IntegerField(null=True, blank=True)

    @staticmethod
    def is_common(raw: str) -> int:
        import hashlib
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return CommonPassword.objects.filter(password_hash=digest).count()

    def __str__(self):
        return self.password_plaintext or self.password_hash[:12]


class Recommendation(models.Model):
    class Meta:
        db_table = 'recommendations'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    analysis = models.ForeignKey(
        AnalyzedPassword, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recommendations',
    )
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=20, default='medium')
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    class Meta:
        db_table = 'reports'
        ordering = ['-generated_at']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, default='full')
    report_format = models.CharField(max_length=10, default='html')
    total_analyses = models.IntegerField(default=0)
    avg_strength = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    weak_passwords = models.IntegerField(default=0)
    medium_passwords = models.IntegerField(default=0)
    strong_passwords = models.IntegerField(default=0)
    common_detected = models.IntegerField(default=0)
    recommendations_count = models.IntegerField(default=0)
    report_data = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)


class LoginAttempt(models.Model):
    class Meta:
        db_table = 'login_attempts'

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    success = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)


class AdminActivityLog(models.Model):
    class Meta:
        db_table = 'admin_activity_log'
        ordering = ['-created_at']

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_targets',
    )
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)