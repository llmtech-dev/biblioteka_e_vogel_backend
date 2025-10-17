from rest_framework import serializers
from .models import Book, BookPage, PageElement
import logging

logger = logging.getLogger(__name__)


class PageElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageElement
        fields = ['type', 'content', 'position']


class BookPageSerializer(serializers.ModelSerializer):
    elements = PageElementSerializer(many=True, read_only=True)

    class Meta:
        model = BookPage
        fields = ['elements']


class BookListSerializer(serializers.ModelSerializer):
    """Serializer për listën e librave (pa pages)"""
    id = serializers.UUIDField(read_only=True)
    coverImage = serializers.SerializerMethodField()
    pdfPath = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'translator', 'category',
            'coverImage', 'pdfPath',
            'notification_sent', 'notification_sent_at', 'notification_count'
        ]

    def get_coverImage(self, obj):
        """Merr URL-në e cover - gjithmonë absolute"""
        try:
            cover_url = obj.get_cover_url()

            # ✅ Kontrollo nëse është bosh
            if not cover_url:
                logger.warning(f"Book {obj.id} has no cover image")
                return ''

            # ✅ Nëse është Cloudinary URL (starts with http)
            if cover_url.startswith('http'):
                logger.info(f"Cover URL (Cloudinary): {cover_url}")
                return cover_url

            # ✅ Nëse është local file, bëje absolute
            request = self.context.get('request')
            if request:
                absolute_url = request.build_absolute_uri(cover_url)
                logger.info(f"Cover URL (local): {absolute_url}")
                return absolute_url

            # ✅ Fallback - build manual URL
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            absolute_url = f"{base_url}{cover_url}"
            logger.warning(f"No request context, using BASE_URL: {absolute_url}")
            return absolute_url

        except Exception as e:
            logger.error(f"Error getting cover image for book {obj.id}: {e}")
            return ''

    def get_pdfPath(self, obj):
        """Merr URL-në e PDF - gjithmonë absolute"""
        try:
            # ✅ Priority për pdf_path nëse është Cloudinary
            if obj.pdf_path and obj.pdf_path.startswith('http'):
                logger.info(f"PDF URL (Cloudinary): {obj.pdf_path}")
                return obj.pdf_path

            # ✅ Nëse ka pdf_file (local)
            if obj.pdf_file:
                request = self.context.get('request')
                if request:
                    absolute_url = request.build_absolute_uri(obj.pdf_file.url)
                    logger.info(f"PDF URL (local): {absolute_url}")
                    return absolute_url

                # Fallback
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                absolute_url = f"{base_url}{obj.pdf_file.url}"
                logger.warning(f"No request context for PDF, using BASE_URL: {absolute_url}")
                return absolute_url

            # ✅ Nëse ka pdf_path por nuk është Cloudinary (local path)
            if obj.pdf_path:
                request = self.context.get('request')
                if request and not obj.pdf_path.startswith('/'):
                    return obj.pdf_path  # Relative path
                elif request:
                    return request.build_absolute_uri(obj.pdf_path)

            logger.warning(f"Book {obj.id} has no PDF")
            return ''

        except Exception as e:
            logger.error(f"Error getting PDF path for book {obj.id}: {e}")
            return ''

    def to_representation(self, instance):
        """Override për të kontrolluar strukturën e output"""
        representation = {
            'id': str(instance.id),
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': self.get_coverImage(instance),
            'pdfPath': self.get_pdfPath(instance),
        }

        # ✅ Log për debugging
        logger.info(f"Serialized book: {instance.title}")
        logger.debug(f"Book data: {representation}")

        return representation


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer i plotë me pages"""
    id = serializers.UUIDField(read_only=True)
    pages = serializers.SerializerMethodField()
    coverImage = serializers.SerializerMethodField()
    pdfPath = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'translator', 'category',
            'coverImage', 'pdfPath', 'pages',
            'notification_sent', 'notification_sent_at', 'notification_count'
        ]

    def get_coverImage(self, obj):
        """Merr URL-në e cover - gjithmonë absolute"""
        try:
            cover_url = obj.get_cover_url()

            if not cover_url:
                return ''

            # Cloudinary URL
            if cover_url.startswith('http'):
                return cover_url

            # Local file me request
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover_url)

            # Fallback
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            return f"{base_url}{cover_url}"

        except Exception as e:
            logger.error(f"Error getting cover for book {obj.id}: {e}")
            return ''

    def get_pdfPath(self, obj):
        """Merr URL-në e PDF - gjithmonë absolute"""
        try:
            # Cloudinary URL
            if obj.pdf_path and obj.pdf_path.startswith('http'):
                return obj.pdf_path

            # Local file
            if obj.pdf_file:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.pdf_file.url)

                # Fallback
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                return f"{base_url}{obj.pdf_file.url}"

            # Local path në pdf_path
            if obj.pdf_path:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.pdf_path)

            return ''

        except Exception as e:
            logger.error(f"Error getting PDF for book {obj.id}: {e}")
            return ''

    def get_pages(self, obj):
        """Formatimi për të matchuar me JSON"""
        try:
            pages = []
            for page in obj.pages.all():
                page_data = {
                    'elements': [
                        {
                            'type': element.type,
                            'content': element.content,
                            'position': element.position
                        }
                        for element in page.elements.all()
                    ]
                }
                pages.append(page_data)

            logger.debug(f"Serialized {len(pages)} pages for book {obj.id}")
            return pages

        except Exception as e:
            logger.error(f"Error serializing pages for book {obj.id}: {e}")
            return []

    def to_representation(self, instance):
        representation = {
            'id': str(instance.id),
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': self.get_coverImage(instance),
            'pdfPath': self.get_pdfPath(instance),
            'pages': self.get_pages(instance)
        }

        logger.info(f"Serialized book detail: {instance.title}")
        logger.debug(f"Full data: {representation}")

        return representation


class BookSerializer(serializers.ModelSerializer):
    """Serializer për create/update (vetëm për admin)"""
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Book
        fields = '__all__'