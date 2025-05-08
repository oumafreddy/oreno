# apps/users/tests/test_otp.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import OTP
from django.core.exceptions import ValidationError

User = get_user_model()

class OTPModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='fredouma@oreno.tech',
            username='testuser',
            password='123@Team*',
            organization=None
        )

    def test_otp_creation(self):
        """Test OTP object creation with valid data"""
        otp = OTP.objects.create(
            user=self.user,
            otp='123456',
            role='admin'
        )
        
        self.assertEqual(otp.otp, '123456')
        self.assertEqual(otp.role, 'admin')
        self.assertFalse(otp.is_verified)
        self.assertEqual(str(otp), f"OTP for {self.user.email} - 123456 (Verified: False)")

    def test_otp_verification(self):
        """Test OTP verification workflow"""
        otp = OTP.objects.create(
            user=self.user,
            otp='654321',
            role='staff'
        )
        
        # Verify OTP
        otp.is_verified = True
        otp.save()
        
        verified_otp = OTP.objects.get(pk=otp.pk)
        self.assertTrue(verified_otp.is_verified)

    def test_otp_user_relationship(self):
        """Test OTP relationship with user model"""
        otp = OTP.objects.create(
            user=self.user,
            otp='112233',
            role='manager'
        )
        
        self.assertEqual(otp.user.email, 'fredouma@oreno.tech')
        self.assertEqual(self.user.otps.count(), 1)

    def test_otp_role_choices(self):
        """Test OTP role field validation"""
        valid_roles = dict(OTP._meta.get_field('role').choices).keys()
        
        # Test valid role
        otp = OTP.objects.create(
            user=self.user,
            otp='445566',
            role='admin'
        )
        self.assertIn(otp.role, valid_roles)
        
        # Test invalid role
        with self.assertRaises(ValidationError):  # Changed to ValidationError
            invalid_otp = OTP(
                user=self.user,
                otp='778899',
                role='invalid_role'
            )
            invalid_otp.full_clean()  # Explicit validation check

class OTPIntegrationTests(TestCase):
    def test_otp_workflow(self):
        """Test complete OTP verification workflow"""
        user = User.objects.create_user(
            email='otpuser@oreno.tech',
            username='otpuser',
            password='testpass123'
        )
        
        # Generate OTP
        otp = OTP.objects.create(
            user=user,
            otp='987654',
            role='admin'
        )
        
        # Verify OTP
        otp.is_verified = True
        otp.save()
        
        # Check verification
        updated_otp = OTP.objects.get(pk=otp.pk)
        self.assertTrue(updated_otp.is_verified)
        self.assertEqual(updated_otp.role, 'admin')

    def test_multiple_otps_per_user(self):
        """Test user can have multiple OTP entries"""
        user = User.objects.create_user(
            email='multi@oreno.tech',
            username='multiuser',
            password='testpass123'
        )
        
        OTP.objects.create(user=user, otp='111111', role='staff')
        OTP.objects.create(user=user, otp='222222', role='admin')
        
        self.assertEqual(user.otps.count(), 2)

    def test_otp_authentication_flow(self):
        """Test OTP verification in authentication context"""
        from django.contrib.auth import authenticate
        
        user = User.objects.create_user(
            email='authuser@oreno.tech',
            username='authuser',
            password='testpass123'
        )
        
        # Create and verify OTP
        otp = OTP.objects.create(
            user=user,
            otp='999999',
            role='staff'
        )
        otp.is_verified = True
        otp.save()
        
        # Authenticate user with OTP
        authenticated_user = authenticate(
            email='authuser@oreno.tech',
            password='testpass123'
        )
        
        self.assertIsNotNone(authenticated_user)
        self.assertTrue(authenticated_user.otps.filter(is_verified=True).exists())