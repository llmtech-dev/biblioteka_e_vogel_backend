# books_api/views.py
# SHTUAR: create, update, delete endpoints për moderatoren
# Vetëm moderatoren/admin mund të shkruajnë

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Book, BookPage, PageElement
from .serializers import (
    BookSerializer, BookDetailSerializer, BookListSerializer,
    BookCreateUpdateSerializer
)
from user_api.permissions import IsModeratorOrAdmin
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet i plotë — lexim për të gjithë, shkrim vetëm moderatore/admin.
    """
    queryset = Book.objects.filter(is_active=True).prefetch_related(
        'pages', 'pages__elements'
    )
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        """Lexim i hapur, shkrim kërkon moderatore."""
        if self.action in ['list', 'retrieve', 'initial_sync',
                           'check_updates', 'sync_status']:
            return [AllowAny()]
        return [IsAuthenticated(), IsModeratorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookCreateUpdateSerializer
        if self.action == 'list':
            return BookListSerializer
        return BookDetailSerializer

    # ─── READ ENDPOINTS (publik) ─────────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BookDetailSerializer(
            instance, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        """GET /api/books/initial_sync/ — sinkronimi fillestar"""
        books = Book.objects.filter(is_active=True).prefetch_related(
            'pages', 'pages__elements'
        )
        serializer = BookDetailSerializer(
            books, many=True, context={'request': request}
        )
        return Response({
            'books': serializer.data,
            'sync_date': timezone.now().isoformat(),
            'count': books.count(),
        })

    @action(detail=False, methods=['get'])
    def check_updates(self, request):
        """GET /api/books/check_updates/?last_sync=... — libra të rinj"""
        last_sync = request.query_params.get('last_sync', None)
        if last_sync:
            try:
                sync_date = datetime.fromisoformat(
                    last_sync.replace('Z', '+00:00')
                )
                books = Book.objects.filter(
                    updated_at__gt=sync_date, is_active=True
                ).prefetch_related('pages', 'pages__elements')
            except ValueError:
                books = Book.objects.filter(is_active=True)
        else:
            books = Book.objects.filter(is_active=True)

        # FIX: Kthe BookDetailSerializer jo BookListSerializer
        serializer = BookDetailSerializer(
            books, many=True, context={'request': request}
        )
        return Response({
            'new_books': serializer.data,
            'count': books.count(),
            'sync_date': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """GET /api/books/sync_status/ — statistika serveri"""
        from django.db.models import Count, Q
        stats = Book.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            notified=Count('id', filter=Q(notification_sent=True)),
        )
        return Response({
            'stats': stats,
            'server_time': timezone.now().isoformat(),
        })

    # ─── WRITE ENDPOINTS (vetëm moderatore) ─────────────────────

    def create(self, request, *args, **kwargs):
        """
        POST /api/books/ — Krijo libër të ri
        Moderatorja dërgon: title, author, translator, category,
                            cover_file (ose cover_image URL),
                            pdf_file (ose pdf_path URL),
                            send_push_now (boolean)
        """
        serializer = BookCreateUpdateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            book = serializer.save()
            logger.info(
                f"📚 Book created: {book.title} by {request.user.email}"
            )
            return Response(
                BookDetailSerializer(book, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /api/books/<id>/ — Përditëso librin
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = BookCreateUpdateSerializer(
            instance, data=request.data, partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            book = serializer.save()
            logger.info(
                f"📝 Book updated: {book.title} by {request.user.email}"
            )
            return Response(
                BookDetailSerializer(book, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/books/<id>/ — Soft delete (is_active=False)
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        logger.info(
            f"🗑️ Book deactivated: {instance.title} by {request.user.email}"
        )
        return Response(
            {"detail": "Libri u çaktivizua me sukses."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsModeratorOrAdmin])
    def send_notification(self, request, pk=None):
        """
        POST /api/books/<id>/send_notification/
        Dërgo push notification manualisht
        """
        book = self.get_object()
        from notifications_api.services import send_book_notification
        try:
            success, response = send_book_notification(book)
            if success:
                return Response({
                    'success': True,
                    'message': f'Njoftimi u dërgua për "{book.title}"',
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

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated, IsModeratorOrAdmin])
    def moderator_dashboard(self, request):
        """
        GET /api/books/moderator_dashboard/ — Dashboard stats për moderatoren
        """
        from django.db.models import Count, Q
        from quizes_api.models import Quiz

        books_stats = Book.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            inactive=Count('id', filter=Q(is_active=False)),
            notified=Count('id', filter=Q(notification_sent=True, is_active=True)),
            not_notified=Count('id', filter=Q(notification_sent=False, is_active=True)),
        )

        quiz_stats = Quiz.objects.aggregate(
            total=Count('id'),
            notified=Count('id', filter=Q(notification_sent=True)),
        )

        recent_books = Book.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]

        recent_quizzes = Quiz.objects.order_by('-created_at')[:5]

        from quizes_api.serializers import QuizSerializer
        return Response({
            'books': {
                **books_stats,
                'recent': BookListSerializer(
                    recent_books, many=True, context={'request': request}
                ).data,
            },
            'quizzes': {
                **quiz_stats,
                'recent': QuizSerializer(
                    recent_quizzes, many=True, context={'request': request}
                ).data,
            },
            'server_time': timezone.now().isoformat(),
        })
