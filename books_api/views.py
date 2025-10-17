from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Book, BookPage, PageElement
from .serializers import BookSerializer, BookDetailSerializer, BookListSerializer
from django.utils import timezone
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


# books_api/views.py

class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.filter(is_active=True)
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        # retrieve action (për single book) duhet të kthejë FULL details me pages
        return BookDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve për të siguruar që kthen pages"""
        instance = self.get_object()

        # Force përdorimin e BookDetailSerializer
        serializer = BookDetailSerializer(instance, context={'request': request})

        # Log për debugging
        logger.info(f"Retrieved book {instance.id} with {instance.pages.count()} pages")

        return Response(serializer.data)

    def get_serializer_context(self):
        """Shto request në context për absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        """Endpoint për sinkronizimin fillestar të librave"""
        books = Book.objects.filter(is_active=True)
        serializer = BookDetailSerializer(books, many=True, context={'request': request})
        return Response({
            'books': serializer.data,
            'sync_date': timezone.now().isoformat()
        })

    @action(detail=False, methods=['get'])
    def check_updates(self, request):
        """Kontrollon për libra të rinj pas një date të caktuar"""
        last_sync = request.query_params.get('last_sync', None)
        if last_sync:
            try:
                sync_date = datetime.fromisoformat(last_sync)
                books = Book.objects.filter(
                    created_at__gt=sync_date,
                    is_active=True
                )
            except:
                books = Book.objects.filter(is_active=True)
        else:
            books = Book.objects.filter(is_active=True)

        serializer = BookListSerializer(books, many=True, context={'request': request})
        return Response({
            'new_books': serializer.data,
            'count': books.count()
        })

    @action(detail=True, methods=['get'])
    def full_details(self, request, pk=None):
        """Get full book details with absolute URLs"""
        book = self.get_object()
        serializer = BookDetailSerializer(book, context={'request': request})

        # Log the response for debugging
        import json
        logger.info(f"Book details response: {json.dumps(serializer.data, indent=2)}")

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """Get sync status and statistics"""
        from django.db.models import Count, Q

        stats = Book.objects.aggregate(
            total_books=Count('id'),
            active_books=Count('id', filter=Q(is_active=True)),
            notified_books=Count('id', filter=Q(notification_sent=True)),
        )

        recent_books = Book.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]

        return Response({
            'stats': stats,
            'recent_books': BookListSerializer(
                recent_books,
                many=True,
                context={'request': request}
            ).data,
            'server_time': timezone.now().isoformat(),
        })

    @action(detail=True, methods=['get'])
    def debug_details(self, request, pk=None):
        """Debug endpoint për të parë të dhënat e plota"""
        book = self.get_object()

        data = {
            'id': str(book.id),
            'title': book.title,
            'pages_count': book.pages.count(),
            'pages': []
        }

        for page in book.pages.all():
            page_data = {
                'page_number': page.page_number,
                'elements_count': page.elements.count(),
                'elements': list(page.elements.values('type', 'content', 'position'))
            }
            data['pages'].append(page_data)

        return Response(data)
