# quiz_api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from .models import Quiz
from .serializers import QuizSerializer
from notifications_api.services import send_quiz_notification


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    pagination_class = None
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def by_book(self, request):
        """Merr kuizet për një libër të caktuar"""
        book_id = request.query_params.get('book_id', None)
        if book_id:
            quizzes = Quiz.objects.filter(book_id=book_id)
            serializer = self.get_serializer(quizzes, many=True)
            return Response(serializer.data)
        return Response(
            {'error': 'book_id is required'},
            status=400
        )

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Merr 5 kuizet e fundit"""
        quizzes = Quiz.objects.order_by('-created_at')[:5]
        serializer = self.get_serializer(quizzes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def send_notification(self, request, pk=None):
        """Manual endpoint për të dërguar notification"""
        quiz = self.get_object()

        try:
            # Check if recently sent
            if quiz.notification_sent_at:
                time_since_last = timezone.now() - quiz.notification_sent_at
                if time_since_last.total_seconds() < 300:  # 5 minutes
                    return Response(
                        {
                            'error': 'Notification was sent recently. Please wait.',
                            'last_sent': quiz.notification_sent_at
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

            success, response = send_quiz_notification(quiz)

            if success:
                return Response({
                    'success': True,
                    'message': 'Notification sent successfully',
                    'response': response,
                    'notification_count': quiz.notification_count
                })
            else:
                return Response(
                    {
                        'success': False,
                        'error': response
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """Kthen statusin e sync për Flutter app"""
        total_quizzes = Quiz.objects.count()
        latest_quiz = Quiz.objects.order_by('-created_at').first()

        return Response({
            'total_quizzes': total_quizzes,
            'latest_update': latest_quiz.created_at if latest_quiz else None,
            'server_time': timezone.now()
        })