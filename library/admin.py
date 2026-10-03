from django.contrib import admin

from .models import Author, Book, Genre, Loan


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_date')
    search_fields = ('first_name', 'last_name')
    ordering = ('last_name', 'first_name')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'id',                    # ← добавили
        'title',
        'publication_year',
        'publisher',
        'total_copies',
        'available_copies',
    )
    list_filter = ('genres', 'publication_year')
    search_fields = ('title', 'isbn', 'publisher', 'authors__last_name')
    filter_horizontal = ('authors', 'genres')
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'book',
        'user',
        'loan_date',
        'due_date',
        'return_date',
        'status',
    )
    list_filter = ('status', 'loan_date', 'due_date')
    search_fields = ('book__title', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'loan_date')
    ordering = ('-loan_date', '-id')
    date_hierarchy = 'loan_date'
