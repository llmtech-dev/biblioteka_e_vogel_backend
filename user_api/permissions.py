# user_api/permissions.py
# Permissions të personalizuara për rolin e moderatores

from rest_framework.permissions import BasePermission


class IsModeratorOrAdmin(BasePermission):
    """
    Lejon akses vetëm për moderatore dhe admin.
    Përdoret në API endpoints që kërkojnë të drejta moderatoreje.
    """
    message = "Duhet të jeni moderatore ose administrator për këtë veprim."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_moderator
        )


class IsAdminOnly(BasePermission):
    """Lejon akses vetëm për admin."""
    message = "Vetëm administratori mund të kryejë këtë veprim."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin_role
        )
