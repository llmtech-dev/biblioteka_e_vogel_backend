from rest_framework import serializers
from .models import Book, BookPage, PageElement


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
    # ✅ UUID do konvertohet automatikisht në string
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
        """Merr URL-në e cover - prioritet për file të ngarkuar"""
        return obj.get_cover_url()

    def get_pdfPath(self, obj):
        """Merr URL-në e PDF - prioritet për file të ngarkuar"""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return obj.pdf_path or ''

    def to_representation(self, instance):
        """Override për të kontrolluar strukturën e output"""
        return {
            'id': str(instance.id),  # ✅ Konverto UUID në string
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': self.get_coverImage(instance),
            'pdfPath': self.get_pdfPath(instance)
        }


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer i plotë me pages"""
    id = serializers.UUIDField(read_only=True)  # ✅ UUID
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
        """Merr URL-në e cover"""
        request = self.context.get('request')
        cover_url = obj.get_cover_url()
        if cover_url and request and not cover_url.startswith('http'):
            return request.build_absolute_uri(cover_url)
        return cover_url

    def get_pdfPath(self, obj):
        """Merr URL-në e PDF"""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return obj.pdf_path or ''

    def get_pages(self, obj):
        """Formatimi për të matchuar me JSON"""
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
        return pages

    def to_representation(self, instance):
        return {
            'id': str(instance.id),  # ✅ Konverto UUID në string
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': self.get_coverImage(instance),
            'pdfPath': self.get_pdfPath(instance),
            'pages': self.get_pages(instance)
        }


class BookSerializer(serializers.ModelSerializer):
    """Serializer për create/update (vetëm për admin)"""
    id = serializers.UUIDField(read_only=True)  # ✅ Read-only për UUID

    class Meta:
        model = Book
        fields = '__all__'