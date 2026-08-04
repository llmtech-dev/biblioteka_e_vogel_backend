# daily_content_api/serializers.py

import logging

from django.conf import settings
from rest_framework import serializers

from .models import DailyContent

logger = logging.getLogger(__name__)


class DailyContentSerializer(serializers.ModelSerializer):
    """Serializer publik — lexim per app-in mobile."""
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DailyContent
        fields = [
            'id', 'type', 'title', 'text', 'source', 'explanation',
            'publish_date', 'created_at',
        ]

    def to_representation(self, instance):
        return {
            'id': str(instance.id),
            'type': instance.type,
            'title': instance.title,
            'text': instance.text,
            'source': instance.source,
            'explanation': instance.explanation,
            'audioUrl': instance.get_audio_url(),
            'publishDate': instance.publish_date.isoformat(),
            'createdAt': instance.created_at.isoformat() if instance.created_at else None,
        }


class DailyContentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per create/update nga moderatorja."""
    audio_file = serializers.FileField(required=False, allow_null=True)

    MAX_AUDIO_SIZE_MB = 20

    class Meta:
        model = DailyContent
        fields = [
            'type', 'title', 'text', 'source', 'explanation',
            'audio_file', 'audio_url', 'publish_date',
            'is_active', 'send_push_now',
        ]

    def validate_audio_file(self, value):
        if value and value.size > self.MAX_AUDIO_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Audio-ja s'duhet të kalojë {self.MAX_AUDIO_SIZE_MB}MB."
            )
        return value

    def _upload_audio(self, audio_file):
        """Ngarko audio te Cloudinary — fallback lokal vetem ne DEBUG,
        njesoj si BookCreateUpdateSerializer (shih books_api/serializers.py)."""
        from books_api.cloudinary_helper import upload_to_cloudinary
        try:
            result = upload_to_cloudinary(audio_file, folder='daily_audio', resource_type='video')
        except Exception as e:
            result = {'success': False, 'error': str(e)}

        if result.get('success'):
            return result['url'], result.get('public_id', '')

        error_msg = result.get('error', 'gabim i panjohur')
        logger.error(f'Cloudinary upload i audios dështoi: {error_msg}')
        if settings.DEBUG:
            return None, None
        raise serializers.ValidationError({
            'audio_file': f"Ngarkimi te Cloudinary dështoi: {error_msg}."
        })

    def create(self, validated_data):
        # DRF trajton nje BooleanField te munguar ne multipart/form-data
        # (jo-partial) si False EKSPLICITE (konvente HTML checkbox), JO si
        # "field i paprekur" — pra validated_data['is_active'] eshte GJITHMONE
        # i pranishem (False nese klienti s'e dergoi). setdefault() s'ndihmon
        # ketu; duhet kontrolluar initial_data (input-i i papërpunuar i
        # klientit) per te ditur nese e dergoi vertet apo jo.
        if 'is_active' not in self.initial_data:
            validated_data['is_active'] = True
        audio_file = validated_data.pop('audio_file', None)
        content = DailyContent(**validated_data)

        if audio_file:
            url, public_id = self._upload_audio(audio_file)
            if url:
                content.audio_url = url
                content.audio_public_id = public_id
            else:
                content.audio_file = audio_file

        content.save()
        return content

    def update(self, instance, validated_data):
        audio_file = validated_data.pop('audio_file', None)

        if audio_file:
            url, public_id = self._upload_audio(audio_file)
            if url:
                instance.audio_url = url
                instance.audio_public_id = public_id
            else:
                instance.audio_file = audio_file

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
