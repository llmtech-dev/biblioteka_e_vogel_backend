from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    bookId = serializers.CharField(source='book_id', read_only=True)
    quizId = serializers.CharField(source='quiz_id', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'description', 'type', 'createdAt',
                  'bookId', 'quizId', 'imageUrl']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': str(instance.id),
            'title': instance.title,
            'description': instance.description,
            'type': instance.type,
            'createdAt': instance.created_at.isoformat(),
            'isRead': False,  # Gjithmonë false pa authentication
            'bookId': instance.book_id if instance.book else None,
            'quizId': instance.quiz_id if instance.quiz else None,
            'imageUrl': instance.image_url or None
        }