from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.filter(is_active=True)
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]  # Pa authentication