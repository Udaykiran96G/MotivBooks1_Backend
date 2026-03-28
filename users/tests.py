from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_regular_registration_weak_password(self):
        """Test that weak passwords are rejected."""
        reg_data = {
            "name": "Test User",
            "email": "testuser_weak@gmail.com",
            "password": "weak",
            "confirmPassword": "weak",
            "phone": "9876543210"
        }
        response = self.client.post('/api/users/register/', reg_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data or response.content.decode())

    def test_regular_registration_strong_password_success(self):
        """Test that strong passwords and valid data succeed."""
        reg_data = {
            "name": "Test User",
            "email": "testuser_strong@gmail.com",
            "password": "StrongPass123!",
            "confirmPassword": "StrongPass123!",
            "phone": "9876543210"
        }
        response = self.client.post('/api/users/register/', reg_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        # Test Login
        login_data = {
            "email": "testuser_strong@gmail.com",
            "password": "StrongPass123!"
        }
        response = self.client.post('/api/users/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_admin_registration_and_login(self):
        """Test admin registration and subsequent login."""
        admin_reg_data = {
            "name": "Admin User",
            "email": "testadmin@gmail.com",
            "password": "AdminPass123!",
            "confirmPassword": "AdminPass123!",
            "phone": "9876543211",
            "is_staff": True
        }
        response = self.client.post('/api/users/admin/register/', admin_reg_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="testadmin@gmail.com")
        self.assertTrue(user.is_staff)
        
        # Test Admin Login
        admin_login_data = {
            "email": "testadmin@gmail.com",
            "password": "AdminPass123!"
        }
        response = self.client.post('/api/users/admin/login/', admin_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['user']['is_staff'])

    def test_password_mismatch(self):
        """Test that mismatched passwords are rejected."""
        reg_data = {
            "name": "Test User",
            "email": "testuser_mismatch@gmail.com",
            "password": "StrongPass123!",
            "confirmPassword": "DifferentPass123!",
            "phone": "9876543210"
        }
        response = self.client.post('/api/users/register/', reg_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', str(response.data))
