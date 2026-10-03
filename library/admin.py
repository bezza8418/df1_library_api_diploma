from django.contrib import admin

from .models import Author, Book, Genre


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
