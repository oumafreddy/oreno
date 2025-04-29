# apps/users/serializers.py
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db.models import Q

from .models import OTP, Profile, OrganizationRole
from organizations.models import Organization

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    Handles serialization and deserialization of User instances for profile operations.
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'avatar', 'date_joined', 'is_active', 'organization'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'is_active', 'organization']

    def update(self, instance, validated_data):
        """
        Update and return an existing user instance, given the validated data.
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
            
        instance.save()
        return instance

class OrganizationRoleSerializer(serializers.ModelSerializer):
    """Serializer for organization roles"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    organization_name = serializers.CharField(source='organization.customer_name', read_only=True)

    class Meta:
        model = OrganizationRole
        fields = ('id', 'user', 'user_email', 'user_name', 'organization', 'organization_name', 'role')
        read_only_fields = ('organization',)

    def validate(self, data):
        user = data.get('user')
        role = data.get('role')
        organization = self.context.get('organization')

        if user and role and organization:
            # Check if user already has this role in the organization
            if OrganizationRole.objects.filter(
                user=user,
                organization=organization,
                role=role
            ).exists():
                raise serializers.ValidationError(_("This user already has this role in the organization."))

            # Check if user belongs to the organization
            if not user.organization == organization:
                raise serializers.ValidationError(_("User does not belong to this organization."))

        return data

class UserSerializer(serializers.ModelSerializer):
    """Base serializer for user data"""
    profile = ProfileSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.customer_name', read_only=True)
    roles = OrganizationRoleSerializer(source='user_roles', many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'organization', 'organization_name', 'role', 'is_active',
            'is_staff', 'date_joined', 'last_login', 'profile', 'roles'
        )
        read_only_fields = ('date_joined', 'last_login')

    def validate_organization(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError(_("Cannot assign user to an inactive organization."))
        return value

class UserRegisterSerializer(UserSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({
                'password2': _("Passwords must match.")
            })
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # Create profile automatically
        Profile.objects.create(user=user)
        # Generate initial OTP
        OTP.objects.create(user=user)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extended token serializer with user data"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        token['organization'] = user.organization.pk if user.organization else None
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include extra user info
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'organization': self.user.organization.pk if self.user.organization else None,
            'role': self.user.role,
            'is_staff': self.user.is_staff,
        }
        return data

class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    code = serializers.CharField(max_length=6, write_only=True)

    def validate_code(self, value):
        try:
            otp = OTP.objects.get(
                user=self.context['request'].user,
                code=value,
                is_verified=False
            )
        except OTP.DoesNotExist:
            raise serializers.ValidationError(_("Invalid code."))

        if otp.is_expired():
            raise serializers.ValidationError(_("Code has expired."))
        return value

    def save(self):
        otp = OTP.objects.get(
            user=self.context['request'].user,
            code=self.validated_data['code']
        )
        otp.is_verified = True
        otp.save()
        return otp

class OTPResendSerializer(serializers.Serializer):
    """Serializer for requesting new OTP"""
    def save(self):
        user = self.context['request'].user
        # Expire old codes
        OTP.objects.filter(
            user=user,
            is_verified=False
        ).update(is_expired=True)
        # Create and send new OTP
        new_otp = OTP.objects.create(user=user)
        new_otp.send_via_email()
        return new_otp

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is incorrect."))
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({
                'new_password2': _("Passwords must match.")
            })
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
