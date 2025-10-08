from rest_framework import serializers
from .models import Quiz, Question, AnswerOption


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['text']

    def to_representation(self, instance):
        return {
            'text': instance.text
        }


class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)  # ✅ UUID
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'correct_option_index']

    def to_representation(self, instance):
        return {
            'id': str(instance.id),  # ✅ Konverto në string
            'text': instance.text,
            'options': [opt['text'] for opt in self.fields['options'].to_representation(instance.options.all())],
            'correctOptionIndex': instance.correct_option_index
        }


class QuizSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)  # ✅ UUID
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'book', 'title', 'questions',
            'notification_sent', 'notification_sent_at', 'notification_count'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': str(instance.id),  # ✅ Konverto në string
            'bookId': str(instance.book_id),  # ✅ Book UUID në string
            'title': instance.title,
            'questions': data['questions']
        }


class QuizCreateSerializer(serializers.ModelSerializer):
    """Për admin - krijimi i quiz"""
    id = serializers.UUIDField(read_only=True)  # ✅ Read-only

    class Meta:
        model = Quiz
        fields = '__all__'