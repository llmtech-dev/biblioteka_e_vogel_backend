# quizes_api/serializers.py — SHTO QuizCreateSerializer
# Zëvendëso skedarin ekzistues me këtë version të plotë

from rest_framework import serializers
from .models import Quiz, Question, AnswerOption
from django.db import transaction


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['text']


class AnswerOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['text', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    def get_options(self, obj):
        return [{"text": opt.text} for opt in obj.options.all().order_by('order')]

    def to_representation(self, instance):
        return {
            'id': str(instance.id),
            'text': instance.text,
            'options': self.get_options(instance),
            'correctOptionIndex': instance.correct_option_index,
        }


class QuestionCreateSerializer(serializers.Serializer):
    """Serializer për krijimin e pyetjeve me opsione të ndërthurura."""
    text = serializers.CharField()
    correct_option_index = serializers.IntegerField(min_value=0)
    order = serializers.IntegerField(default=0)
    options = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=2,
        max_length=4
    )

    def validate_options(self, value):
        for opt in value:
            if 'text' not in opt or not opt['text'].strip():
                raise serializers.ValidationError(
                    "Çdo opsion duhet të ketë 'text' jo bosh."
                )
        return value

    def validate(self, data):
        if data['correct_option_index'] >= len(data['options']):
            raise serializers.ValidationError(
                "correct_option_index duhet të jetë brenda numrit të opsioneve."
            )
        return data


class QuizSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'book', 'title', 'questions',
            'notification_sent', 'notification_sent_at', 'notification_count',
            'created_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': str(instance.id),
            'bookId': str(instance.book_id),
            'title': instance.title,
            'questions': data['questions'],
            'createdAt': instance.created_at.isoformat() if instance.created_at else None,
        }


class QuizCreateSerializer(serializers.Serializer):
    """
    Serializer i plotë për krijimin e quiz me pyetje dhe opsione.
    Mbështet transaksion atomik — nëse diçka dështon, asgjë nuk ruhet.
    """
    book = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    send_push_now = serializers.BooleanField(default=False)
    questions = QuestionCreateSerializer(many=True, min_length=1)

    def validate_book(self, value):
        from books_api.models import Book
        try:
            book = Book.objects.get(id=value, is_active=True)
            return book
        except Book.DoesNotExist:
            raise serializers.ValidationError(
                "Libri nuk u gjet ose nuk është aktiv."
            )

    @transaction.atomic
    def save(self, **kwargs):
        book = self.validated_data['book']
        title = self.validated_data['title']
        send_push = self.validated_data.get('send_push_now', False)
        questions_data = self.validated_data['questions']

        # Krijo quiz
        quiz = Quiz.objects.create(
            book=book,
            title=title,
            send_push_now=send_push,
        )

        # Krijo pyetjet dhe opsionet
        for q_data in questions_data:
            question = Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                correct_option_index=q_data['correct_option_index'],
                order=q_data.get('order', 0),
            )
            for i, opt_data in enumerate(q_data['options']):
                AnswerOption.objects.create(
                    question=question,
                    text=opt_data['text'],
                    order=i,
                )

        return quiz
