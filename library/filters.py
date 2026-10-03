import django_filters

from .models import Book


class BookFilter(django_filters.FilterSet):
    """Расширенный фильтр для книг."""

    publication_year_min = django_filters.NumberFilter(
        field_name='publication_year',
        lookup_expr='gte',
        label='Год издания от',
    )
    publication_year_max = django_filters.NumberFilter(
        field_name='publication_year',
        lookup_expr='lte',
        label='Год издания до',
    )
    available = django_filters.BooleanFilter(
        method='filter_available',
        label='Только доступные',
    )

    class Meta:
        model = Book
        fields = (
            'publication_year',
            'publisher',
            'authors',
            'genres',
        )

    def filter_available(self, queryset, name, value):
        """Фильтр: только книги, у которых есть доступные экземпляры."""
        if value:
            return queryset.filter(available_copies__gt=0)
        return queryset
