from rest_framework import serializers

from .models import AnalyzedPassword, LoginAttempt, Recommendation, Report, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'fullname', 'username', 'email', 'is_admin', 'is_active', 'last_login')


class UserCreateSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    security_question = serializers.CharField(required=False, allow_blank=True)
    security_answer = serializers.CharField(required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AnalyzedPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyzedPassword
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = '__all__'