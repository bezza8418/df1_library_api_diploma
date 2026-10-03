from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


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


class Loan(models.Model):
    """Выдача книги читателю."""

    STATUS_ISSUED = 'issued'
    STATUS_RETURNED = 'returned'
    STATUS_LOST = 'lost'
    STATUS_CHOICES = [
        (STATUS_ISSUED, 'Выдана'),
        (STATUS_RETURNED, 'Возвращена'),
        (STATUS_LOST, 'Потеряна'),
    ]

    DEFAULT_LOAN_PERIOD_DAYS = 14

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Читатель',
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Книга',
    )
    loan_date = models.DateField('Дата выдачи', auto_now_add=True)
    due_date = models.DateField('Плановая дата возврата', null=True, blank=True)
    return_date = models.DateField('Дата возврата', null=True, blank=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ISSUED,
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Выдача'
        verbose_name_plural = 'Выдачи'
        ordering = ['-loan_date', '-id']

    def __str__(self):
        return f'{self.book.title} → {self.user.email} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        """При создании, если не указан due_date — ставим loan_date + 14 дней."""
        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(
                days=self.DEFAULT_LOAN_PERIOD_DAYS
            )
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Просрочена ли выдача (не возвращена и due_date в прошлом)."""
        if self.status != self.STATUS_ISSUED:
            return False
        return self.due_date < timezone.now().date()

    @property
    def effective_status(self):
        """
        Эффективный статус с учётом просрочки.
        Используется в сериализаторе, чтобы показать "overdue" без хранения в БД.
        """
        if self.is_overdue:
            return 'overdue'
        return self.status

    def return_book(self):
        """Вернуть книгу."""
        if self.status != self.STATUS_ISSUED:
            raise ValueError(
                f'Нельзя вернуть выдачу со статусом "{self.get_status_display()}".'
            )

        self.status = self.STATUS_RETURNED
        self.return_date = timezone.now().date()
        self.save(update_fields=['status', 'return_date', 'updated_at'])

        book = self.book
        book.available_copies = min(
            book.available_copies + 1,
            book.total_copies,
        )
        book.save(update_fields=['available_copies', 'updated_at'])

    def mark_lost(self):
        """Отметить книгу как потерянную."""
        if self.status != self.STATUS_ISSUED:
            raise ValueError(
                f'Нельзя отметить как потерянную выдачу со статусом "{self.get_status_display()}".'
            )

        self.status = self.STATUS_LOST
        self.save(update_fields=['status', 'updated_at'])

        book = self.book
        book.total_copies = max(book.total_copies - 1, 0)
        book.save(update_fields=['total_copies', 'updated_at'])

    # ====== БИЗНЕС-ЛОГИКА ======

    def return_book(self):
        """
        Вернуть книгу.
        - Проверяет, что выдача активна.
        - Ставит return_date = сегодня.
        - Меняет статус на 'returned'.
        - Увеличивает available_copies у книги.
        """
        if self.status != self.STATUS_ISSUED:
            raise ValueError(
                f'Нельзя вернуть выдачу со статусом "{self.get_status_display()}".'
            )

        self.status = self.STATUS_RETURNED
        self.return_date = timezone.now().date()
        self.save(update_fields=['status', 'return_date', 'updated_at'])

        # Возвращаем экземпляр в фонд
        book = self.book
        book.available_copies = min(
            book.available_copies + 1,
            book.total_copies,
        )
        book.save(update_fields=['available_copies', 'updated_at'])

    def mark_lost(self):
        """
        Отметить книгу как потерянную.
        - Проверяет, что выдача активна.
        - Меняет статус на 'lost'.
        - НЕ возвращает экземпляр в фонд (книга потеряна).
        - Уменьшает total_copies (книга выбывает из фонда).
        """
        if self.status != self.STATUS_ISSUED:
            raise ValueError(
                f'Нельзя отметить как потерянную выдачу со статусом "{self.get_status_display()}".'
            )

        self.status = self.STATUS_LOST
        self.save(update_fields=['status', 'updated_at'])

        # Книга потеряна — выбывает из фонда
        book = self.book
        book.total_copies = max(book.total_copies - 1, 0)
        book.save(update_fields=['total_copies', 'updated_at'])