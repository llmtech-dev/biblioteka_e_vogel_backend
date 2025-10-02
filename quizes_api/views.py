from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Quiz
from .serializers import QuizSerializer


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [AllowAny]  # Pa authentication

    @action(detail=False, methods=['get'])
    def by_book(self, request):
        """Merr kuizet për një libër të caktuar"""
        book_id = request.query_params.get('book_id', None)
        if book_id:
            quizzes = Quiz.objects.filter(book_id=book_id)
            serializer = self.get_serializer(quizzes, many=True)
            return Response(serializer.data)
        return Response({'error': 'book_id is required'},
                        status=400)