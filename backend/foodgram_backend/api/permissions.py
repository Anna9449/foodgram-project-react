from rest_framework import permissions


class IsAuthorAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return request.method in permissions.SAFE_METHODS
        return True

    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user
                or request.user.is_superuser
                or request.method in permissions.SAFE_METHODS)
