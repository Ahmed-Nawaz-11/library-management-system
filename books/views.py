from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.db.models import Q
from .models import Author, Category, Book
from .serializers import AuthorSerializer, CategorySerializer, BookSerializer
from .permissions import IsAdminOrLibrarian, IsAdmin
from accounts.pagination import CustomPagination

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    res = {"success": True, "message": message}
    if data is not None:
        if isinstance(data, dict) and 'count' in data and 'results' in data:
            res["data"] = data
        else:
            res["data"] = data
    return Response(res, status=status_code)

def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    res = {"success": False, "message": message}
    if errors is not None:
        res["errors"] = errors
    return Response(res, status=status_code)

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrLibrarian]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response("Categories retrieved successfully", self.paginator.get_paginated_response(serializer.data).data['data'])
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Categories retrieved successfully", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Category created successfully", serializer.data, status.HTTP_201_CREATED)
        return error_response("Failed to create category", serializer.errors)

class AuthorListCreateView(generics.ListCreateAPIView):
    queryset = Author.objects.all().order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrLibrarian]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response("Authors retrieved successfully", self.paginator.get_paginated_response(serializer.data).data['data'])
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Authors retrieved successfully", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response("Author created successfully", serializer.data, status.HTTP_201_CREATED)
        return error_response("Failed to create author", serializer.errors)

class BookListCreateView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrLibrarian]
    pagination_class = CustomPagination

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
            return success_response("Books retrieved successfully", self.paginator.get_paginated_response(serializer.data).data['data'])
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Books retrieved successfully", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set available_copies equal to total_copies on creation
            validated_data = serializer.validated_data
            if 'total_copies' in validated_data:
                serializer.save(available_copies=validated_data['total_copies'])
            else:
                serializer.save()
            return success_response("Book created successfully", serializer.data, status.HTTP_201_CREATED)
        return error_response("Failed to create book", serializer.errors)

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
        return success_response("Book retrieved successfully", serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response("Book updated successfully", serializer.data)
        return error_response("Failed to update book", serializer.errors)

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
                "Cannot delete book because it has active borrow records.", 
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        instance.delete()
        return success_response("Book deleted successfully", status_code=status.HTTP_200_OK)
