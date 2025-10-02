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

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'translator', 'category',
                  'cover_image', 'pdf_path']  # Përdor cover_image jo coverImage

    # Override field names për të matchuar me Flutter
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': instance.cover_image,  # Konverto në camelCase këtu
            'pdfPath': instance.pdf_path or ''
        }


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer i plotë me pages"""
    pages = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'translator', 'category',
                  'cover_image', 'pdf_path', 'pages']  # Përdor cover_image

    def get_pages(self, obj):
        # Formatimi për të matchuar me JSON tuaj
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
            'id': instance.id,
            'title': instance.title,
            'author': instance.author,
            'translator': instance.translator,
            'category': instance.category,
            'coverImage': instance.cover_image,  # Konverto në camelCase këtu
            'pdfPath': instance.pdf_path or '',
            'pages': self.get_pages(instance)
        }


class BookSerializer(serializers.ModelSerializer):
    """Serializer për create/update (vetëm për admin)"""

    class Meta:
        model = Book
        fields = '__all__'