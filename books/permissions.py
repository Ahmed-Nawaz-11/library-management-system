from rest_framework import permissions

class IsAdminOrLibrarian(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow safe methods for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # For non-safe methods, check if authenticated and role is admin or librarian
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'librarian']
        )

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )
