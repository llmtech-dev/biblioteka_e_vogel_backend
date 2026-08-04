from django.conf import settings
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
        """
        Kthen URL-në e cover.
        - Cloudinary / URL e jashtme (fillon me http) → absolute URL, nuk ndryshon kurrë
        - Fajll lokal → PATH RELATIV (/media/covers/xxx.jpg)
          Flutter e ndërton URL-në e plotë me AppConfig.baseUrl
          Kjo do të thotë: ndryshimi i ngrok-ut nuk e prish SQLite-n e Flutter-it
        """
        try:
            cover_url = obj.get_cover_url()
            if not cover_url:
                return ''
            # Cloudinary ose URL e jashtme absolute — kthe ashtu siç është
            if cover_url.startswith('http'):
                return cover_url
            # Fajll lokal — kthe vetëm path-in relativ
            # p.sh. /media/covers/test.jpg  (jo https://ngrok-xxx.app/media/...)
            return cover_url  # tashmë është relative: /media/covers/...
        except Exception as e:
            logger.error(f"Error getting cover image for book {obj.id}: {e}")
            return ''

    def get_pdfPath(self, obj):
        """
        Kthen URL-në e PDF.
        - Cloudinary / URL e jashtme → absolute URL
        - Fajll lokal → PATH RELATIV (/media/pdfs/xxx.pdf)
        """
        try:
            if obj.pdf_path and obj.pdf_path.startswith('http'):
                return obj.pdf_path
            if obj.pdf_file:
                return obj.pdf_file.url   # p.sh. /media/pdfs/test.pdf
            if obj.pdf_path:
                return obj.pdf_path
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
        """Kthe URL absolute (Cloudinary) ose path relativ (lokal)."""
        try:
            cover_url = obj.get_cover_url()
            if not cover_url:
                return ''
            if cover_url.startswith('http'):
                return cover_url
            return cover_url
        except Exception as e:
            logger.error(f"Error getting cover for book {obj.id}: {e}")
            return ''

    def get_pdfPath(self, obj):
        """Kthe URL absolute (Cloudinary) ose path relativ (lokal)."""
        try:
            if obj.pdf_path and obj.pdf_path.startswith('http'):
                return obj.pdf_path
            if obj.pdf_file:
                return obj.pdf_file.url
            if obj.pdf_path:
                return obj.pdf_path
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


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer për create/update nga moderatorja.
    Mbështet upload direkt të file-ve (cover_file, pdf_file)
    OSE URL-ve nga Cloudinary (cover_image, pdf_path).
    """
    cover_file = serializers.ImageField(required=False, allow_null=True)
    pdf_file = serializers.FileField(required=False, allow_null=True)

    MAX_PDF_SIZE_MB = 50
    MAX_COVER_SIZE_MB = 5

    class Meta:
        model = Book
        fields = [
            'title', 'author', 'translator', 'category',
            'cover_file', 'cover_image',
            'pdf_file', 'pdf_path',
            'is_active', 'send_push_now',
        ]

    def validate_pdf_file(self, value):
        if value:
            if value.size > self.MAX_PDF_SIZE_MB * 1024 * 1024:
                raise serializers.ValidationError(
                    f"PDF-ja s'duhet të kalojë {self.MAX_PDF_SIZE_MB}MB."
                )
            if not value.name.lower().endswith('.pdf'):
                raise serializers.ValidationError(
                    "Skedari duhet të jetë në format PDF (.pdf)."
                )
        return value

    def validate_cover_file(self, value):
        if value and value.size > self.MAX_COVER_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Kopertina s'duhet të kalojë {self.MAX_COVER_SIZE_MB}MB."
            )
        return value

    def validate(self, attrs):
        # Vetëm në krijim: libri duhet të ketë PDF, ose file i ngarkuar ose URL.
        # Në update s'e detyrojmë sepse instanca ekzistuese mund ta ketë tashmë.
        if self.instance is None:
            has_pdf = attrs.get('pdf_file') or attrs.get('pdf_path')
            if not has_pdf:
                raise serializers.ValidationError({
                    'pdf_file': "Libri duhet të ketë një PDF — ngarko një skedar (pdf_file) ose jep pdf_path.",
                })
        return attrs

    def _cloudinary_upload(self, file_obj, folder, resource_type, field_label):
        """
        Ngarko te Cloudinary. Ne prodhim (DEBUG=False) kjo eshte e detyrueshme:
        hosting si Render ka disk jo te perhershem, çdo deploy/restart fshin
        ruajtjen lokale — nje "fallback i heshtur" atje do te thoshte librat
        e humbin PDF-ne/kopertinen ne heshtje. Fallback lokal lejohet vetem
        ne zhvillim (DEBUG=True, p.sh. makina jote).
        Kthen (url, public_id) kur ka sukses, ose (None, None) kur duhet
        rene ne fallback lokal (vetem ne DEBUG).
        """
        from books_api.cloudinary_helper import upload_to_cloudinary
        try:
            result = upload_to_cloudinary(
                file_obj, folder=folder, resource_type=resource_type
            )
        except Exception as e:
            result = {'success': False, 'error': str(e)}

        if result.get('success'):
            return result['url'], result.get('public_id', '')

        error_msg = result.get('error', 'gabim i panjohur')
        logger.error(f'Cloudinary upload failed ({field_label}): {error_msg}')
        if settings.DEBUG:
            return None, None
        raise serializers.ValidationError({
            field_label: (
                f"Ngarkimi te Cloudinary deshtoi: {error_msg}. "
                "Ne prodhim ruajtja lokale s'lejohet (disku s'eshte i perhershem)."
            )
        })

    def create(self, validated_data):
        # DRF trajton nje BooleanField te munguar ne multipart/form-data
        # (jo-partial) si False EKSPLICITE (konvente HTML checkbox), JO si
        # "field i paprekur" — validated_data['is_active'] eshte gjithmone
        # i pranishem (False nese klienti s'e dergoi). Kontrollo initial_data
        # (input i papërpunuar) per te ditur nese klienti e dergoi vertet.
        # Flutter e dergon eksplicit 'is_active': 'true' (shih
        # moderator_api_service.dart uploadBook), kjo eshte mbrojtje shtese.
        if 'is_active' not in self.initial_data:
            validated_data['is_active'] = True
        cover_file = validated_data.pop('cover_file', None)
        pdf_file = validated_data.pop('pdf_file', None)
        book = Book(**validated_data)

        if cover_file:
            url, public_id = self._cloudinary_upload(
                cover_file, 'book_covers', 'image', 'cover_file'
            )
            if url:
                book.cover_image = url
                book.cover_public_id = public_id
            else:
                book.cover_file = cover_file

        if pdf_file:
            url, public_id = self._cloudinary_upload(
                pdf_file, 'book_pdfs', 'raw', 'pdf_file'
            )
            if url:
                book.pdf_path = url
                book.pdf_public_id = public_id
            else:
                book.pdf_file = pdf_file

        book.save()
        return book

    def update(self, instance, validated_data):
        cover_file = validated_data.pop('cover_file', None)
        pdf_file = validated_data.pop('pdf_file', None)

        if cover_file:
            url, public_id = self._cloudinary_upload(
                cover_file, 'book_covers', 'image', 'cover_file'
            )
            if url:
                instance.cover_image = url
                instance.cover_public_id = public_id
            else:
                instance.cover_file = cover_file

        if pdf_file:
            url, public_id = self._cloudinary_upload(
                pdf_file, 'book_pdfs', 'raw', 'pdf_file'
            )
            if url:
                instance.pdf_path = url
                instance.pdf_public_id = public_id
            else:
                instance.pdf_file = pdf_file

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
