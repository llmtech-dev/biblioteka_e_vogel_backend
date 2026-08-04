# daily_content_api/views.py

from datetime import datetime, timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone

from .models import DailyContent
from .serializers import DailyContentSerializer, DailyContentCreateUpdateSerializer
from user_api.permissions import IsModeratorOrAdmin
import logging

logger = logging.getLogger(__name__)


class DailyContentViewSet(viewsets.ModelViewSet):
    """
    Lexim i hapur per te gjithe, shkrim vetem moderatore/admin —
    njesoj si BookViewSet/QuizViewSet.
    """
    queryset = DailyContent.objects.filter(is_active=True)
    serializer_class = DailyContentSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'today', 'initial_sync', 'check_updates']:
            return [AllowAny()]
        return [IsAuthenticated(), IsModeratorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DailyContentCreateUpdateSerializer
        return DailyContentSerializer

    # ─── READ ENDPOINTS (publike) ────────────────────────────────

    @action(detail=False, methods=['get'])
    def today(self, request):
        """GET /api/daily-content/today/ — permbajtja e sotme (ose e fundit e publikuar)."""
        content = (
            self.get_queryset()
            .filter(publish_date__lte=timezone.localdate())
            .order_by('-publish_date')
            .first()
        )
        if not content:
            return Response(
                {'detail': 'Nuk ka ende përmbajtje ditore.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DailyContentSerializer(content).data)

    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        """GET /api/daily-content/initial_sync/ — arkivi (30 dite te fundit) per cache offline."""
        since = timezone.localdate() - timedelta(days=30)
        items = self.get_queryset().filter(
            publish_date__gte=since, publish_date__lte=timezone.localdate()
        ).order_by('-publish_date')
        return Response({
            'items': DailyContentSerializer(items, many=True).data,
            'sync_date': timezone.now().isoformat(),
            'count': items.count(),
        })

    @action(detail=False, methods=['get'])
    def check_updates(self, request):
        """GET /api/daily-content/check_updates/?last_sync=... — permbajtje e re qe nga last_sync."""
        last_sync = request.query_params.get('last_sync', None)
        items = self.get_queryset().filter(publish_date__lte=timezone.localdate())
        if last_sync:
            try:
                if last_sync.isdigit():
                    sync_date = datetime.fromtimestamp(int(last_sync) / 1000)
                else:
                    sync_date = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                items = items.filter(created_at__gt=sync_date)
            except (ValueError, OSError):
                pass
        items = items.order_by('-publish_date')
        return Response({
            'new_items': DailyContentSerializer(items, many=True).data,
            'count': items.count(),
        })

    # ─── WRITE ENDPOINTS (vetem moderatore) ──────────────────────

    def create(self, request, *args, **kwargs):
        serializer = DailyContentCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            content = serializer.save()
            logger.info(f"📿 Daily content created: {content} by {request.user.email}")
            return Response(
                DailyContentSerializer(content).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DailyContentCreateUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        if serializer.is_valid():
            content = serializer.save()
            logger.info(f"📝 Daily content updated: {content} by {request.user.email}")
            return Response(DailyContentSerializer(content).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(
            {'detail': 'Përmbajtja u çaktivizua me sukses.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsModeratorOrAdmin])
    def send_notification(self, request, pk=None):
        content = self.get_object()
        from notifications_api.services import send_daily_content_notification
        try:
            if content.notification_sent_at:
                delta = (timezone.now() - content.notification_sent_at).total_seconds()
                if delta < 300:
                    return Response(
                        {'error': 'Prit 5 minuta para njoftimit tjetër.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
            success, response = send_daily_content_notification(content)
            if success:
                return Response({'success': True, 'message': 'Njoftimi u dërgua.'})
            return Response(
                {'success': False, 'error': str(response)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
