from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.db.models import Q
from .models import Author, Category, Book
from .serializers import AuthorSerializer, CategorySerializer, BookSerializer
from library_management_system.permissions import IsAdminOrLibrarian, IsAdmin
from library_management_system.utils import success_response, error_response

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdminOrLibrarian()]
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = {
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "current_page": self.paginator.page.number,
                "total_pages": self.paginator.page.paginator.num_pages
            }
            return success_response(data=serializer.data, message="Categories retrieved successfully", pagination=pagination_data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Categories retrieved successfully")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="Category created successfully", status=status.HTTP_201_CREATED)
        return error_response(message="Failed to create category", errors=serializer.errors)

class AuthorListCreateView(generics.ListCreateAPIView):
    queryset = Author.objects.all().order_by('id')
    serializer_class = AuthorSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdminOrLibrarian()]
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = {
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "current_page": self.paginator.page.number,
                "total_pages": self.paginator.page.paginator.num_pages
            }
            return success_response(data=serializer.data, message="Authors retrieved successfully", pagination=pagination_data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Authors retrieved successfully")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="Author created successfully", status=status.HTTP_201_CREATED)
        return error_response(message="Failed to create author", errors=serializer.errors)

class BookListCreateView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdminOrLibrarian()]


    def get_queryset(self):
        queryset = Book.objects.all().order_by('-id')
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        available = self.request.query_params.get('available', None)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(author__name__icontains=search) | 
                Q(isbn__icontains=search)
            )
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if available is not None:
            if available.lower() == 'true':
                queryset = queryset.filter(available_copies__gt=0)
            elif available.lower() == 'false':
                queryset = queryset.filter(available_copies=0)
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = {
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "current_page": self.paginator.page.number,
                "total_pages": self.paginator.page.paginator.num_pages
            }
            return success_response(data=serializer.data, message="Books retrieved successfully", pagination=pagination_data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Books retrieved successfully")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set available_copies equal to total_copies on creation
            validated_data = serializer.validated_data
            if 'total_copies' in validated_data:
                serializer.save(available_copies=validated_data['total_copies'])
            else:
                serializer.save()
            return success_response(data=serializer.data, message="Book created successfully", status=status.HTTP_201_CREATED)
        return error_response(message="Failed to create book", errors=serializer.errors)

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdmin()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAdminOrLibrarian()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Book retrieved successfully")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="Book updated successfully")
        return error_response(message="Failed to update book", errors=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the book has active borrow records
        from borrowing.models import BorrowRecord
        active_borrows = BorrowRecord.objects.filter(
            book=instance, 
            status__in=['borrowed', 'overdue']
        ).exists()
        
        if active_borrows:
            return error_response(
                message="Cannot delete book because it has active borrow records.", 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        instance.delete()
        return success_response(message="Book deleted successfully", status=status.HTTP_200_OK)
