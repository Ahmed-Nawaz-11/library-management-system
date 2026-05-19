from django.urls import path
from .views import CategoryListCreateView, AuthorListCreateView, AuthorDetailView, BookListCreateView, BookDetailView

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category_list_create'),
    path('authors/', AuthorListCreateView.as_view(), name='author_list_create'),
    path('authors/<int:pk>/', AuthorDetailView.as_view(), name='author_detail'),
    path('books/', BookListCreateView.as_view(), name='book_list_create'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
]
