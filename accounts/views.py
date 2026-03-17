from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer
from .permissions import IsAdminUserChoice
from .pagination import CustomPagination

User = get_user_model()

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    res = {"success": True, "message": message}
    if data is not None:
        res["data"] = data
    return Response(res, status=status_code)

def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    res = {"success": False, "message": message}
    if errors is not None:
        res["errors"] = errors
    return Response(res, status=status_code)

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
            return success_response("User registered successfully", data, status.HTTP_201_CREATED)
        return error_response("Registration failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return success_response("Login successful", serializer.validated_data)
        except Exception as e:
            return error_response("Invalid credentials", {"detail": str(e)}, status.HTTP_401_UNAUTHORIZED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return success_response("User profile retrieved successfully", serializer.data)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        # manual update since fields are read_only in serializer
        if 'email' in request.data:
            user.email = request.data['email']
        if 'phone' in request.data:
            user.phone = request.data['phone']
        user.save()
        serializer = self.get_serializer(user)
        return success_response("User profile updated successfully", serializer.data)
        
class MemberListView(generics.ListAPIView):
    queryset = User.objects.filter(role='member').order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserChoice]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response("Members retrieved successfully", serializer.data)

class SuspendMemberView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserChoice]

    def post(self, request, pk, *args, **kwargs):
        try:
            member = User.objects.get(pk=pk, role='member')
            member.is_suspended = not member.is_suspended
            member.save()
            status_str = "suspended" if member.is_suspended else "unsuspended"
            return success_response(f"Member successfully {status_str}", UserSerializer(member).data)
        except User.DoesNotExist:
            return error_response("Member not found", status_code=status.HTTP_404_NOT_FOUND)

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
            return success_response("Password changed successfully")
        return error_response("Password change failed", serializer.errors)
