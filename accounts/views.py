from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer, LoginSerializer
from library_management_system.permissions import IsAdmin, IsAdminOrLibrarian
from library_management_system.utils import success_response, error_response

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            data = {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
            return success_response(data=data, message="User registered successfully", status=status.HTTP_201_CREATED)
        return error_response(message="Registration failed", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Invalid credentials", errors=serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        }
        
        return success_response(data=data, message="Login successful")

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return success_response(data=serializer.data, message="User profile retrieved successfully")

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        # manual update since fields are read_only in serializer
        if 'email' in request.data:
            user.email = request.data['email']
        if 'phone' in request.data:
            user.phone = request.data['phone']
        user.save()
        serializer = self.get_serializer(user)
        return success_response(data=serializer.data, message="User profile updated successfully")
        
class MemberListView(generics.ListAPIView):
    queryset = User.objects.filter(role='member').order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrLibrarian]
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
            return success_response(data=serializer.data, message="Members retrieved successfully", pagination=pagination_data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Members retrieved successfully")

class SuspendMemberView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk, *args, **kwargs):
        try:
            member = User.objects.get(pk=pk, role='member')
            member.is_suspended = not member.is_suspended
            member.save()
            status_str = "suspended" if member.is_suspended else "unsuspended"
            return success_response(data=UserSerializer(member).data, message=f"Member successfully {status_str}")
        except User.DoesNotExist:
            return error_response(message="Member not found", status=status.HTTP_404_NOT_FOUND)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = self.get_object()
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return success_response(message="Password changed successfully")
        return error_response(message="Password change failed", errors=serializer.errors)
