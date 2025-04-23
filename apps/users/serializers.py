# apps/users/serializers.py
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import OTP, Profile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'organization', 'role', 'password', 'password2')
        read_only_fields = ('id',)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({
                'password2': "Passwords must match."
            })
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # create profile automatically
        Profile.objects.create(user=user)
        # generate initial OTP
        OTP.objects.create(user=user)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extend the default to include user fields in the response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        token['organization'] = user.organization.pk if user.organization else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # include extra user info
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'organization': self.user.organization.pk if self.user.organization else None,
            'role': self.user.role,
        }
        return data

class OTPVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, write_only=True)

    def validate_code(self, value):
        try:
            otp = OTP.objects.get(user=self.context['request'].user, code=value)
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid code.")

        if otp.is_expired():
            raise serializers.ValidationError("Code has expired.")
        return value

    def save(self):
        otp = OTP.objects.get(user=self.context['request'].user, code=self.validated_data['code'])
        otp.verified = True
        otp.verified_at = timezone.now()
        otp.save()
        return otp

class OTPResendSerializer(serializers.Serializer):
    """
    Endpoint to request a new OTP code.
    """
    def save(self):
        user = self.context['request'].user
        # expire old codes
        OTP.objects.filter(user=user, verified=False).update(expired=True)
        # create and send new
        new_otp = OTP.objects.create(user=user)
        new_otp.send_via_email()
        return new_otp
