from django.core.validators import MinValueValidator
from django.db import models


class Author(models.Model):
    """Автор книги."""

    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    biography = models.TextField('Биография', blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name'],
                name='unique_author_full_name',
            ),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Genre(models.Model):
    """Жанр книги."""

    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга в библиотеке."""

    title = models.CharField('Название', max_length=255)
    authors = models.ManyToManyField(
        Author,
        related_name='books',
        verbose_name='Авторы',
    )
    genres = models.ManyToManyField(
        Genre,
        related_name='books',
        verbose_name='Жанры',
    )
    isbn = models.CharField(
        'ISBN',
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )
    publication_year = models.PositiveIntegerField(
        'Год издания',
        null=True,
        blank=True,
    )
    publisher = models.CharField('Издательство', max_length=200, blank=True)
    description = models.TextField('Описание', blank=True)
    total_copies = models.PositiveIntegerField(
        'Всего экземпляров',
        default=1,
        validators=[MinValueValidator(1)],
    )
    available_copies = models.PositiveIntegerField(
        'Доступно экземпляров',
        default=1,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['title']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(available_copies__lte=models.F('total_copies')),
                name='available_copies_lte_total_copies',
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        """Есть ли доступные экземпляры."""
        return self.available_copies > 0
