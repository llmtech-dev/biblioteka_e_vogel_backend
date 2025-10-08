from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.filter(is_active=True)
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register_token(self, request):
        """Regjistron FCM token nga Flutter app"""
        token = request.data.get('token')
        # Ruaj token në database nëse do përdorësh për target specifik
        return Response({'status': 'Token registered'})