from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Book, BookPage, PageElement
from notifications_api.services import send_book_notification


class PageElementInline(admin.TabularInline):
    model = PageElement
    extra = 1
    fields = ['type', 'content', 'position', 'image_file', 'preview_image']
    readonly_fields = ['preview_image']

    def preview_image(self, obj):
        if obj.image_file:
            return mark_safe(f'<img src="{obj.image_file.url}" width="100" />')
        return "Nuk ka imazh"

    preview_image.short_description = 'Preview'


class BookPageInline(admin.TabularInline):
    model = BookPage
    extra = 1
    show_change_link = True
    fields = ['page_number']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'short_id',
        'title',
        'author',
        'category',
        'cover_preview',
        'is_active',
        'notification_status',
        'notification_sent_at',
        'notification_count',
        'created_at'
    ]
    list_filter = [
        'category',
        'is_active',
        'notification_sent',
        'created_at',
        'notification_sent_at'
    ]
    search_fields = ['title', 'author', 'translator', 'id']

    inlines = [BookPageInline]

    # ✅ ID nuk duhet të jetë editable
    readonly_fields = [
        'id',  # ✅ Shto këtë
        'created_at',
        'updated_at',
        'notification_sent',
        'notification_sent_at',
        'notification_count',
        'cover_preview_large'
    ]

    fieldsets = (
        ('Informacioni Bazë', {
            'fields': ('id', 'title', 'author', 'translator', 'category'),  # id është readonly
            'description': 'ID-ja gjenerohet automatikisht'
        }),
        ('Media - Zgjedh njërën ose tjetrën', {
            'fields': (
                'cover_file',
                'cover_image',
                'cover_preview_large',
                'pdf_file',
                'pdf_path',
            ),
            'description': 'Mund të ngarkosh file OSE të vendosësh URL. Nëse ngarkon file, URL-ja do gjenerohet automatikisht.'
        }),
        ('Push-notification', {
            'fields': ('send_push_now',),
            'description': 'Shënoje ⇧ nëse do që të dërgohet njoftim menjëherë',
        }),
        ('Statusi', {
            'fields': ('is_active', 'version')
        }),
        ('Tracking i Njoftimeve', {
            'fields': (
                'notification_sent',
                'notification_sent_at',
                'notification_count'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['send_notification_for_books', 'reset_notification_status']

    # ✅ Shto metodë për të shfaqur UUID të shkurtër
    def short_id(self, obj):
        """Shfaq 8 karakteret e para të UUID"""
        return str(obj.id)[:8] + '...'

    short_id.short_description = 'ID'

    def cover_preview(self, obj):
        """Preview i vogël në listë"""
        url = obj.get_cover_url()
        if url:
            return mark_safe(f'<img src="{url}" width="50" height="70" style="object-fit: cover;" />')
        return "❌"

    cover_preview.short_description = '📷'

    def cover_preview_large(self, obj):
        """Preview i madh në formë"""
        url = obj.get_cover_url()
        if url:
            return mark_safe(f'<img src="{url}" width="200" style="border: 1px solid #ddd; padding: 5px;" />')
        return "Nuk ka imazh"

    cover_preview_large.short_description = 'Preview i Cover'

    def notification_status(self, obj):
        """Shfaq statusin e njoftimit"""
        if obj.notification_sent:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Dërguar</span>'
            )
        return format_html(
            '<span style="color: orange;">⏳ Jo ende</span>'
        )

    notification_status.short_description = '📨 Statusi'

    def save_model(self, request, obj, form, change):
        """Dërgo notification kur shtohet libër i ri"""
        is_new = not change

        # Nëse cover_file është ngarkuar dhe cover_image është bosh
        if obj.cover_file and not obj.cover_image:
            super().save_model(request, obj, form, change)
            obj.cover_image = request.build_absolute_uri(obj.cover_file.url)
            obj.save(update_fields=['cover_image'])
        else:
            super().save_model(request, obj, form, change)

        # Dërgo notification vetëm për libra të rinj dhe aktiv
        if is_new and obj.is_active:
            try:
                success, response = send_book_notification(obj)
                if success:
                    messages.success(
                        request,
                        f'✅ Njoftimi për librin u dërgua: {response}'
                    )
                else:
                    messages.warning(
                        request,
                        f'⚠️ Libri u ruajt por njoftimi nuk u dërgua: {response}'
                    )
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Gabim në dërgimin e njoftimit: {str(e)}'
                )

    def send_notification_for_books(self, request, queryset):
        """Dërgo notification për librat e zgjedhur"""
        sent = 0
        failed = 0
        already_sent = 0
        inactive = 0

        for book in queryset:
            if not book.is_active:
                inactive += 1
                continue

            if book.notification_sent:
                already_sent += 1
                continue

            try:
                success, response = send_book_notification(book)
                if success:
                    sent += 1
                else:
                    failed += 1
                    messages.warning(
                        request,
                        f'⚠️ Libri "{book.title}": {response}'
                    )
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f'❌ Gabim për "{book.title}": {str(e)}'
                )

        if sent > 0:
            messages.success(request, f'✅ U dërguan {sent} njoftime të reja')
        if already_sent > 0:
            messages.info(request, f'ℹ️ {already_sent} libra kishin njoftim të dërguar tashmë')
        if inactive > 0:
            messages.warning(request, f'⚠️ {inactive} libra nuk janë aktivë')
        if failed > 0:
            messages.error(request, f'❌ {failed} njoftime dështuan')

    send_notification_for_books.short_description = "📚 Dërgo njoftim për librat e zgjedhur"

    def reset_notification_status(self, request, queryset):
        """Reseto statusin e njoftimit (për testing)"""
        count = queryset.update(
            notification_sent=False,
            notification_sent_at=None
        )
        messages.success(request, f'🔄 U resetua statusi për {count} libra')

    reset_notification_status.short_description = "🔄 Reseto statusin e njoftimeve"


@admin.register(BookPage)
class BookPageAdmin(admin.ModelAdmin):
    list_display = ['book', 'page_number', 'element_count']
    list_filter = ['book']
    search_fields = ['book__title']
    inlines = [PageElementInline]
    ordering = ['book', 'page_number']

    def element_count(self, obj):
        count = obj.elements.count()
        return format_html(
            '<span style="color: {};">{} elemente</span>',
            'green' if count > 0 else 'gray',
            count
        )

    element_count.short_description = 'Elemente'


@admin.register(PageElement)
class PageElementAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'type', 'page', 'position', 'image_preview']
    list_filter = ['type', 'page__book']
    search_fields = ['content', 'page__book__title']
    readonly_fields = ['image_preview']

    def short_content(self, obj):
        if obj.type == 'text':
            return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
        return f"[Image]"

    short_content.short_description = 'Përmbajtja'

    def image_preview(self, obj):
        if obj.image_file:
            return mark_safe(f'<img src="{obj.image_file.url}" width="200" />')
        return "Nuk ka imazh"

    image_preview.short_description = 'Preview'