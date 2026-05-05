from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserRefreshToken
from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer, LoginSerializer
from library_management_system.permissions import IsAdmin, IsAdminOrLibrarian
from library_management_system.utils import success_response, error_response

User = get_user_model()

# ─── Helpers ────────────────────────────────────────────────────────────────

COOKIE_ACCESS_MAX_AGE  = 60 * 60           # 1 hour  (seconds)
COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24 * 7  # 7 days  (seconds)


def _set_auth_cookies(response, access_token, refresh_token):
    """Attach HTTP-only auth cookies to *response*."""
    cookie_kwargs = dict(httponly=True, samesite='Lax', secure=False)
    response.set_cookie('access_token',  str(access_token),  max_age=COOKIE_ACCESS_MAX_AGE,  **cookie_kwargs)
    response.set_cookie('refresh_token', str(refresh_token), max_age=COOKIE_REFRESH_MAX_AGE, **cookie_kwargs)


def _delete_auth_cookies(response):
    """Remove both auth cookies from *response*."""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


# ─── Register ───────────────────────────────────────────────────────────────

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


# ─── Login ───────────────────────────────────────────────────────────────────

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid credentials",
                errors=serializer.errors,
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        # ── Persist refresh token in DB (clean up revoked ones first) ──
        UserRefreshToken.objects.filter(user=user, is_revoked=True).delete()
        UserRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=timezone.now() + timedelta(days=7)
        )

        # ── Build response — tokens go in cookies, NOT the body ──
        data = {
            "user": {
                "id":           user.id,
                "username":     user.username,
                "email":        user.email,
                "role":         user.role,
                "is_suspended": user.is_suspended,
            }
        }
        response = success_response(data=data, message="Login successful")
        _set_auth_cookies(response, access, refresh)
        return response


# ─── Cookie Token Refresh ────────────────────────────────────────────────────

class CookieTokenRefreshView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token_string = request.COOKIES.get('refresh_token')

        if not token_string:
            return error_response(
                message="No refresh token found. Please login again.",
                status=status.HTTP_401_UNAUTHORIZED
            )

        stored = UserRefreshToken.objects.filter(token=token_string).first()
        if not stored or not stored.is_valid():
            return error_response(
                message="Session expired. Please login again.",
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh     = RefreshToken(stored.token)
            new_access  = str(refresh.access_token)
        except Exception:
            return error_response(
                message="Session expired. Please login again.",
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = success_response(data={}, message="Token refreshed successfully")
        response.set_cookie(
            'access_token', new_access,
            max_age=COOKIE_ACCESS_MAX_AGE,
            httponly=True, samesite='Lax', secure=False
        )
        return response


# ─── Logout ──────────────────────────────────────────────────────────────────

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        token_string = request.COOKIES.get('refresh_token')
        if token_string:
            stored = UserRefreshToken.objects.filter(token=token_string).first()
            if stored:
                stored.is_revoked = True
                stored.save()

        response = success_response(data={}, message="Logged out successfully")
        _delete_auth_cookies(response)
        return response


# ─── Profile ─────────────────────────────────────────────────────────────────

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
        if 'email' in request.data:
            user.email = request.data['email']
        if 'phone' in request.data:
            user.phone = request.data['phone']
        user.save()
        serializer = self.get_serializer(user)
        return success_response(data=serializer.data, message="User profile updated successfully")


# ─── Member management ───────────────────────────────────────────────────────

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
                "count":       self.paginator.page.paginator.count,
                "next":        self.paginator.get_next_link(),
                "previous":    self.paginator.get_previous_link(),
                "current_page": self.paginator.page.number,
                "total_pages": self.paginator.page.paginator.num_pages,
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


# ─── Change password ─────────────────────────────────────────────────────────

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
