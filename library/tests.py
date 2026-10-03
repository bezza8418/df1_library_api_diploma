from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Author, Genre

User = get_user_model()


# ==================== МОДЕЛИ ====================

class AuthorModelTest(TestCase):
    """Тесты модели Author."""

    def test_str_returns_full_name(self):
        author = Author.objects.create(first_name='Лев', last_name='Толстой')
        self.assertEqual(str(author), 'Толстой Лев')

    def test_ordering_by_last_name(self):
        Author.objects.create(first_name='Фёдор', last_name='Достоевский')
        Author.objects.create(first_name='Лев', last_name='Толстой')
        authors = list(Author.objects.all())
        self.assertEqual(authors[0].last_name, 'Достоевский')
        self.assertEqual(authors[1].last_name, 'Толстой')

    def test_unique_full_name(self):
        Author.objects.create(first_name='Лев', last_name='Толстой')
        with self.assertRaises(Exception):
            Author.objects.create(first_name='Лев', last_name='Толстой')


class GenreModelTest(TestCase):
    """Тесты модели Genre."""

    def test_str_returns_name(self):
        genre = Genre.objects.create(name='Роман')
        self.assertEqual(str(genre), 'Роман')

    def test_unique_name(self):
        Genre.objects.create(name='Роман')
        with self.assertRaises(Exception):
            Genre.objects.create(name='Роман')


# ==================== API: АВТОРЫ ====================

class AuthorAPITest(APITestCase):
    """Тесты API авторов."""

    def setUp(self):
        self.librarian = User.objects.create_user(
            email='librarian@test.com',
            password='StrongPass123!',
            role='librarian',
        )
        self.reader = User.objects.create_user(
            email='reader@test.com',
            password='StrongPass123!',
            role='reader',
        )
        self.author = Author.objects.create(
            first_name='Лев',
            last_name='Толстой',
            biography='Русский писатель',
            birth_date='1828-09-09',
        )
        self.list_url = reverse('library:author-list')
        self.detail_url = reverse('library:author-detail', args=[self.author.id])

    def test_list_unauthorized(self):
        """Без токена — 401."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_reader(self):
        """Читатель видит список."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_as_reader_forbidden(self):
        """Читатель не может создавать — 403."""
        self.client.force_authenticate(user=self.reader)
        data = {'first_name': 'Антон', 'last_name': 'Чехов'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_librarian(self):
        """Библиотекарь создаёт автора — 201."""
        self.client.force_authenticate(user=self.librarian)
        data = {'first_name': 'Антон', 'last_name': 'Чехов'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.count(), 2)

    def test_update_as_reader_forbidden(self):
        """Читатель не может обновлять — 403."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.patch(self.detail_url, {'first_name': 'Иван'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_librarian(self):
        """Библиотекарь обновляет автора — 200."""
        self.client.force_authenticate(user=self.librarian)
        response = self.client.patch(self.detail_url, {'first_name': 'Иван'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, 'Иван')

    def test_delete_as_reader_forbidden(self):
        """Читатель не может удалять — 403."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_librarian(self):
        """Библиотекарь удаляет автора — 204."""
        self.client.force_authenticate(user=self.librarian)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Author.objects.count(), 0)

    def test_search_by_last_name(self):
        """Поиск по фамилии."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'search': 'Толстой'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_last_name(self):
        """Фильтрация по точному совпадению фамилии."""
        Author.objects.create(first_name='Антон', last_name='Чехов')
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'last_name': 'Чехов'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['last_name'], 'Чехов')

    def test_ordering(self):
        """Сортировка по дате рождения (по убыванию)."""
        Author.objects.create(
            first_name='Антон', last_name='Чехов', birth_date='1860-01-29',
        )
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'ordering': '-birth_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['last_name'], 'Чехов')  # 1860 > 1828


# ==================== API: ЖАНРЫ ====================

class GenreAPITest(APITestCase):
    """Тесты API жанров."""

    def setUp(self):
        self.librarian = User.objects.create_user(
            email='librarian@test.com',
            password='StrongPass123!',
            role='librarian',
        )
        self.reader = User.objects.create_user(
            email='reader@test.com',
            password='StrongPass123!',
            role='reader',
        )
        self.genre = Genre.objects.create(name='Роман')
        self.list_url = reverse('library:genre-list')
        self.detail_url = reverse('library:genre-detail', args=[self.genre.id])

    def test_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_reader(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_as_reader_forbidden(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(self.list_url, {'name': 'Поэзия'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_librarian(self):
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(self.list_url, {'name': 'Поэзия'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_search(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'search': 'Ром'})
        self.assertEqual(response.data['count'], 1)
