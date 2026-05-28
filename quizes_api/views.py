# quizes_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from datetime import datetime
from .models import Quiz
from .serializers import QuizSerializer
from notifications_api.services import send_quiz_notification


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    pagination_class = None
    permission_classes = [AllowAny]

    # ─── Initial Sync (Flutter e kërkon këtë) ────────────────────────
    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        """
        Endpoint për sinkronizimin fillestar të kuizeve nga Flutter app.
        GET /api/quizzes/initial_sync/
        Response: { "quizzes": [...], "sync_date": "..." }
        """
        quizzes = Quiz.objects.all().order_by('-created_at')
        serializer = self.get_serializer(quizzes, many=True)
        return Response({
            'quizzes': serializer.data,
            'sync_date': timezone.now().isoformat(),
            'count': quizzes.count(),
        })

    # ─── Check Updates (Flutter e kërkon këtë) ───────────────────────
    @action(detail=False, methods=['get'])
    def check_updates(self, request):
        """
        Kontrollon për kuize të reja pas datës last_sync.
        GET /api/quizzes/check_updates/?last_sync=2025-01-01T00:00:00
        Response: { "new_quizzes": [...], "count": N }
        """
        last_sync = request.query_params.get('last_sync', None)
        if last_sync:
            try:
                # Mbështet si ISO format ashtu edhe timestamp numerik
                if last_sync.isdigit():
                    sync_date = datetime.fromtimestamp(int(last_sync) / 1000)
                else:
                    sync_date = datetime.fromisoformat(
                        last_sync.replace('Z', '+00:00')
                    )
                quizzes = Quiz.objects.filter(created_at__gt=sync_date)
            except (ValueError, OSError):
                quizzes = Quiz.objects.all()
        else:
            quizzes = Quiz.objects.all()

        quizzes = quizzes.order_by('-created_at')
        serializer = self.get_serializer(quizzes, many=True)
        return Response({
            'new_quizzes': serializer.data,
            'count': quizzes.count(),
        })

    # ─── By Book ─────────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def by_book(self, request):
        """
        Merr kuizet për një libër të caktuar.
        GET /api/quizzes/by_book/?book_id=<uuid>
        """
        book_id = request.query_params.get('book_id', None)
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        quizzes = Quiz.objects.filter(book_id=book_id)
        serializer = self.get_serializer(quizzes, many=True)
        return Response(serializer.data)

    # ─── Latest ──────────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Merr 5 kuizet e fundit."""
        quizzes = Quiz.objects.order_by('-created_at')[:5]
        serializer = self.get_serializer(quizzes, many=True)
        return Response(serializer.data)

    # ─── Sync Status ─────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """Kthen statusin e sync për Flutter app."""
        total_quizzes = Quiz.objects.count()
        latest_quiz = Quiz.objects.order_by('-created_at').first()

        return Response({
            'total_quizzes': total_quizzes,
            'latest_update': latest_quiz.created_at if latest_quiz else None,
            'server_time': timezone.now(),
        })

    # ─── Send Notification (Admin only) ──────────────────────────────
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def send_notification(self, request, pk=None):
        """Manual endpoint për të dërguar notification."""
        quiz = self.get_object()

        try:
            if quiz.notification_sent_at:
                time_since_last = timezone.now() - quiz.notification_sent_at
                if time_since_last.total_seconds() < 300:
                    return Response(
                        {
                            'error': 'Notification was sent recently. Please wait.',
                            'last_sent': quiz.notification_sent_at,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

            success, response = send_quiz_notification(quiz)

            if success:
                return Response({
                    'success': True,
                    'message': 'Notification sent successfully',
                    'response': response,
                    'notification_count': quiz.notification_count,
                })
            else:
                return Response(
                    {'success': False, 'error': response},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
