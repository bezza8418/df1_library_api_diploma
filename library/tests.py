from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Author, Book, Genre

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


# ==================== API: КНИГИ ====================

class BookModelTest(TestCase):
    """Тесты модели Book."""

    def setUp(self):
        self.author = Author.objects.create(first_name='Лев', last_name='Толстой')
        self.genre = Genre.objects.create(name='Роман')
        self.book = Book.objects.create(
            title='Война и мир',
            total_copies=3,
            available_copies=3,
        )
        self.book.authors.add(self.author)
        self.book.genres.add(self.genre)

    def test_str_returns_title(self):
        self.assertEqual(str(self.book), 'Война и мир')

    def test_is_available_true(self):
        self.assertTrue(self.book.is_available)

    def test_is_available_false(self):
        self.book.available_copies = 0
        self.book.save()
        self.assertFalse(self.book.is_available)

    def test_ordering_by_title(self):
        Book.objects.create(title='Анна Каренина', total_copies=1, available_copies=1)
        books = list(Book.objects.all())
        self.assertEqual(books[0].title, 'Анна Каренина')
        self.assertEqual(books[1].title, 'Война и мир')

    def test_m2m_author(self):
        self.assertIn(self.author, self.book.authors.all())

    def test_m2m_genre(self):
        self.assertIn(self.genre, self.book.genres.all())

    def test_isbn_optional(self):
        """ISBN может быть пустым."""
        book = Book.objects.create(title='Без ISBN', total_copies=1, available_copies=1)
        self.assertIsNone(book.isbn)

    def test_isbn_unique(self):
        """ISBN уникален, если указан."""
        self.book.isbn = '978-5-04-116563-5'
        self.book.save()
        with self.assertRaises(Exception):
            Book.objects.create(
                title='Другая книга',
                isbn='978-5-04-116563-5',
                total_copies=1,
                available_copies=1,
            )

    def test_available_copies_check_constraint(self):
        """БД не даёт сохранить available_copies > total_copies."""
        with self.assertRaises(Exception):
            Book.objects.create(
                title='Плохая книга',
                total_copies=2,
                available_copies=5,
            )


class BookAPITest(APITestCase):
    """Тесты API книг."""

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
        self.author = Author.objects.create(first_name='Лев', last_name='Толстой')
        self.genre = Genre.objects.create(name='Роман')
        self.book = Book.objects.create(
            title='Война и мир',
            isbn='978-5-17-090465-5',
            publication_year=1869,
            total_copies=3,
            available_copies=3,
        )
        self.book.authors.add(self.author)
        self.book.genres.add(self.genre)

        self.list_url = reverse('library:book-list')
        self.detail_url = reverse('library:book-detail', args=[self.book.id])

    def test_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_reader_with_nested_data(self):
        """В ответе — вложенные авторы и жанры."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertIsInstance(result['authors'], list)
        self.assertIsInstance(result['genres'], list)
        self.assertEqual(result['authors'][0]['last_name'], 'Толстой')
        self.assertEqual(result['genres'][0]['name'], 'Роман')

    def test_create_as_reader_forbidden(self):
        self.client.force_authenticate(user=self.reader)
        data = {
            'title': 'Анна Каренина',
            'authors': [self.author.id],
            'genres': [self.genre.id],
            'total_copies': 1,
            'available_copies': 1,
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_librarian(self):
        self.client.force_authenticate(user=self.librarian)
        data = {
            'title': 'Анна Каренина',
            'authors': [self.author.id],
            'genres': [self.genre.id],
            'total_copies': 2,
            'available_copies': 2,
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_create_invalid_isbn(self):
        """Невалидный ISBN → 400."""
        self.client.force_authenticate(user=self.librarian)
        data = {
            'title': 'Книга',
            'authors': [self.author.id],
            'genres': [self.genre.id],
            'isbn': 'abc123',
            'total_copies': 1,
            'available_copies': 1,
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', response.data)

    def test_create_future_year(self):
        """Год издания в будущем → 400."""
        self.client.force_authenticate(user=self.librarian)
        data = {
            'title': 'Книга из будущего',
            'authors': [self.author.id],
            'genres': [self.genre.id],
            'publication_year': 2099,
            'total_copies': 1,
            'available_copies': 1,
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('publication_year', response.data)

    def test_create_available_greater_than_total(self):
        """available_copies > total_copies → 400."""
        self.client.force_authenticate(user=self.librarian)
        data = {
            'title': 'Плохая книга',
            'authors': [self.author.id],
            'genres': [self.genre.id],
            'total_copies': 2,
            'available_copies': 5,
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('available_copies', response.data)

    def test_filter_by_genre(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'genres': self.genre.id})
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_author(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'authors': self.author.id})
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_year_range(self):
        """Диапазон годов."""
        Book.objects.create(
            title='Книга 2000',
            publication_year=2000,
            total_copies=1,
            available_copies=1,
        )
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(
            self.list_url,
            {'publication_year_min': 1800, 'publication_year_max': 1900},
        )
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Война и мир')

    def test_filter_available(self):
        """Только доступные книги."""
        unavailable = Book.objects.create(
            title='Недоступная',
            total_copies=1,
            available_copies=0,
        )
        unavailable.authors.add(self.author)

        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'available': 'true'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Война и мир')

    def test_search_by_title(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'search': 'Война'})
        self.assertEqual(response.data['count'], 1)

    def test_search_by_author_name(self):
        """Поиск по фамилии автора."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'search': 'Толстой'})
        self.assertEqual(response.data['count'], 1)

    def test_ordering_by_year(self):
        Book.objects.create(
            title='Книга 2000',
            publication_year=2000,
            total_copies=1,
            available_copies=1,
        )
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url, {'ordering': '-publication_year'})
        results = response.data['results']
        self.assertEqual(results[0]['title'], 'Книга 2000')

    def test_delete_as_librarian(self):
        self.client.force_authenticate(user=self.librarian)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
