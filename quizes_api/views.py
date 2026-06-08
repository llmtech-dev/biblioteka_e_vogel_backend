# quizes_api/views.py
# SHTUAR: create, update, delete endpoints për moderatoren

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import datetime
from .models import Quiz, Question, AnswerOption
from .serializers import QuizSerializer, QuizCreateSerializer
from user_api.permissions import IsModeratorOrAdmin
import logging

logger = logging.getLogger(__name__)


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet i plotë — lexim për të gjithë, shkrim vetëm moderatore/admin.
    """
    queryset = Quiz.objects.all().select_related('book').prefetch_related(
        'questions', 'questions__options'
    )
    serializer_class = QuizSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'initial_sync',
                           'check_updates', 'by_book', 'latest',
                           'sync_status']:
            return [AllowAny()]
        return [IsAuthenticated(), IsModeratorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateSerializer
        return QuizSerializer

    # ─── READ ENDPOINTS ──────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        quizzes = self.get_queryset().order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)
        return Response({
            'quizzes': serializer.data,
            'sync_date': timezone.now().isoformat(),
            'count': quizzes.count(),
        })

    @action(detail=False, methods=['get'])
    def check_updates(self, request):
        last_sync = request.query_params.get('last_sync', None)
        if last_sync:
            try:
                if last_sync.isdigit():
                    sync_date = datetime.fromtimestamp(int(last_sync) / 1000)
                else:
                    sync_date = datetime.fromisoformat(
                        last_sync.replace('Z', '+00:00')
                    )
                quizzes = self.get_queryset().filter(created_at__gt=sync_date)
            except (ValueError, OSError):
                quizzes = self.get_queryset()
        else:
            quizzes = self.get_queryset()

        quizzes = quizzes.order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)
        return Response({
            'new_quizzes': serializer.data,
            'count': quizzes.count(),
        })

    @action(detail=False, methods=['get'])
    def by_book(self, request):
        book_id = request.query_params.get('book_id')
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        quizzes = self.get_queryset().filter(book_id=book_id)
        return Response(QuizSerializer(quizzes, many=True).data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        quizzes = self.get_queryset().order_by('-created_at')[:5]
        return Response(QuizSerializer(quizzes, many=True).data)

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        total = Quiz.objects.count()
        latest = Quiz.objects.order_by('-created_at').first()
        return Response({
            'total_quizzes': total,
            'latest_update': latest.created_at if latest else None,
            'server_time': timezone.now(),
        })

    # ─── WRITE ENDPOINTS (vetëm moderatore) ─────────────────────

    def create(self, request, *args, **kwargs):
        """
        POST /api/quizzes/
        Body: {
          "book": "<uuid>",
          "title": "...",
          "send_push_now": true,
          "questions": [
            {
              "text": "Pyetja?",
              "correct_option_index": 0,
              "order": 0,
              "options": [
                {"text": "Opsioni A", "order": 0},
                {"text": "Opsioni B", "order": 1},
                ...
              ]
            }
          ]
        }
        """
        serializer = QuizCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            quiz = serializer.save()
            logger.info(
                f"🎯 Quiz created: {quiz.title} by {request.user.email}"
            )
            return Response(
                QuizSerializer(quiz).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        instance.delete()
        logger.info(f"🗑️ Quiz deleted: {title} by {request.user.email}")
        return Response(
            {"detail": f'Kuizi "{title}" u fshi me sukses.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsModeratorOrAdmin])
    def send_notification(self, request, pk=None):
        quiz = self.get_object()
        from notifications_api.services import send_quiz_notification
        try:
            # Rate limit check
            if quiz.notification_sent_at:
                delta = (timezone.now() - quiz.notification_sent_at).total_seconds()
                if delta < 300:
                    return Response(
                        {'error': 'Prit 5 minuta para njoftimit tjetër.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
            success, response = send_quiz_notification(quiz)
            if success:
                return Response({
                    'success': True,
                    'message': f'Njoftimi u dërgua për "{quiz.title}"',
                })
            return Response(
                {'success': False, 'error': str(response)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
