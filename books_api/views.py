from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Book, BookPage, PageElement
from .serializers import BookSerializer, BookDetailSerializer, BookListSerializer
from django.utils import timezone

class BookViewSet(viewsets.ReadOnlyModelViewSet):  # ReadOnly për public
    queryset = Book.objects.filter(is_active=True)
    permission_classes = [AllowAny]  # Pa authentication

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BookDetailSerializer

    @action(detail=False, methods=['get'])
    def initial_sync(self, request):
        """Endpoint për sinkronizimin fillestar të librave"""
        books = Book.objects.filter(is_active=True)
        serializer = BookDetailSerializer(books, many=True)
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

        serializer = BookListSerializer(books, many=True)
        return Response({
            'new_books': serializer.data,
            'count': books.count()
        })