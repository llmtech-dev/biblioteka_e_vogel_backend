from rest_framework import serializers
from .models import Quiz, Question, AnswerOption


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['text']

    def to_representation(self, instance):
        # Kthe vetëm text-in si në JSON tuaj
        return {
            'text': instance.text
        }


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'correct_option_index']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'text': instance.text,
            'options': [opt['text'] for opt in self.fields['options'].to_representation(instance.options.all())],
            'correctOptionIndex': instance.correct_option_index
        }


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'book', 'title', 'questions']  # Përdor 'book' jo 'bookId'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': instance.id,
            'bookId': instance.book_id,  # book_id jo book
            'title': instance.title,
            'questions': data['questions']
        }


class QuizCreateSerializer(serializers.ModelSerializer):
    """Për admin - krijimi i quiz"""

    class Meta:
        model = Quiz
        fields = '__all__'