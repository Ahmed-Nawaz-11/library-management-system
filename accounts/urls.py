from django.urls import path
from .views import (
    RegisterView, LoginView, UserProfileView,
    MemberListView, SuspendMemberView, ChangePasswordView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('members/', MemberListView.as_view(), name='member_list'),
    path('members/<int:pk>/suspend/', SuspendMemberView.as_view(), name='suspend_member'),
]
