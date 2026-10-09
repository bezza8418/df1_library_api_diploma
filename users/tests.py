from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


# ==================== МОДЕЛИ ====================


class UserModelTest(APITestCase):
    """Тесты модели User."""

    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertEqual(user.role, "reader")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="StrongPass123!")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_str(self):
        user = User.objects.create_user(email="test@example.com", password="pass")
        self.assertEqual(str(user), "test@example.com")

    def test_is_librarian_property(self):
        user = User.objects.create_user(email="lib@example.com", password="pass", role="librarian")
        self.assertTrue(user.is_librarian)
        self.assertFalse(user.is_reader)

    def test_is_reader_property(self):
        user = User.objects.create_user(email="reader@example.com", password="pass", role="reader")
        self.assertTrue(user.is_reader)
        self.assertFalse(user.is_librarian)


# ==================== РЕГИСТРАЦИЯ ====================


class RegisterAPITest(APITestCase):
    """Тесты эндпоинта регистрации."""

    def setUp(self):
        self.url = reverse("users:register")

    def test_register_success(self):
        data = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Иван",
            "last_name": "Тестов",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data["role"], "reader")

    def test_register_password_mismatch(self):
        data = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="existing@example.com", password="pass")
        data = {
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_as_librarian_forbidden(self):
        data = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "librarian",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_register_weak_password(self):
        data = {
            "email": "new@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ==================== JWT ====================


class JWTAuthTest(APITestCase):
    """Тесты JWT-авторизации."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        self.token_url = reverse("users:token_obtain_pair")
        self.refresh_url = reverse("users:token_refresh")

    def test_obtain_token_success(self):
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_wrong_password(self):
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "WrongPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_nonexistent_user(self):
        response = self.client.post(
            self.token_url,
            {"email": "nobody@example.com", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
        )
        refresh = response.data["refresh"]

        response = self.client.post(self.refresh_url, {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_with_invalid_token(self):
        response = self.client.post(self.refresh_url, {"refresh": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ==================== ПРОФИЛЬ ====================


class ProfileAPITest(APITestCase):
    """Тесты эндпоинта /me/."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
            first_name="Иван",
            last_name="Тестов",
        )
        self.url = reverse("users:me")

    def test_get_profile_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "user@example.com")

    def test_update_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.url,
            {"first_name": "Пётр", "last_name": "Обновлённый"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Пётр")

    def test_cannot_change_email(self):
        """Email — read-only."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {"email": "hacker@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "user@example.com")

    def test_cannot_change_role(self):
        """Роль — read-only."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {"role": "librarian"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "reader")
