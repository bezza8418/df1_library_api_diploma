from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BookViewSet, GenreViewSet

app_name = 'library'

router = DefaultRouter()
router.register('authors', AuthorViewSet, basename='author')
router.register('genres', GenreViewSet, basename='genre')
router.register('books', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
]
