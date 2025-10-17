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

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'notification_sent',
        'notification_sent_at',
        'notification_count',
        'cover_preview_large',
        'cover_public_id',
        'pdf_public_id'
    ]

    fieldsets = (
        ('Informacioni Bazë', {
            'fields': ('id', 'title', 'author', 'translator', 'category'),
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
            'description': 'Mund të ngarkosh file OSE të vendosësh URL.'
        }),
        ('Statusi & Njoftimi', {
            'fields': ('is_active', 'version', 'send_push_now'),
            'description': '🔔 Shëno "Dërgo njoftim" për të njoftuar përdoruesit për këtë libër'
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

    actions = [
        'send_notification_active_books',
        'send_notification_all_selected',
        'reset_notification_status',
        'activate_and_notify'
    ]

    inlines = [BookPageInline]

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
            return mark_safe(f'''
                <img src="{url}" width="200" style="border: 1px solid #ddd; padding: 5px;" /><br>
                <small>URL: {url}</small>
            ''')
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

    # books_api/admin.py - në metodën get_form

    def get_form(self, request, obj=None, **kwargs):
        """Customize form për të treguar status të ndryshëm"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.notification_sent:
            times_sent = obj.notification_count
            last_sent = obj.notification_sent_at.strftime('%d/%m/%Y %H:%M') if obj.notification_sent_at else 'N/A'

            form.base_fields['send_push_now'].help_text = (
                f'📢 Njoftimi është dërguar {times_sent} herë. '
                f'Hera e fundit: {last_sent}. '
                f'✓ Shëno për të dërguar njoftim përditësimi.'
            )
        elif obj:
            form.base_fields['send_push_now'].help_text = (
                '✓ Shëno për të dërguar push notification kur ruhet libri'
            )
        else:
            form.base_fields['send_push_now'].help_text = (
                '✓ Shëno për të njoftuar përdoruesit për librin e ri'
            )

        return form

    def save_model(self, request, obj, form, change):
        """Save me Cloudinary upload"""
        # Cloudinary upload për cover
        if 'cover_file' in form.changed_data and obj.cover_file:
            from books_api.cloudinary_helper import upload_to_cloudinary

            result = upload_to_cloudinary(
                obj.cover_file,
                folder='book_covers',
                resource_type='image'
            )

            if result['success']:
                obj.cover_image = result['url']
                obj.cover_public_id = result['public_id']
                messages.success(request, f"✅ Cover u ngarkua në Cloudinary")
            else:
                messages.error(request, f"❌ Problem me Cloudinary: {result['error']}")

        # Cloudinary upload për PDF
        if 'pdf_file' in form.changed_data and obj.pdf_file:
            from books_api.cloudinary_helper import upload_to_cloudinary

            result = upload_to_cloudinary(
                obj.pdf_file,
                folder='book_pdfs',
                resource_type='raw'
            )

            if result['success']:
                obj.pdf_path = result['url']
                obj.pdf_public_id = result['public_id']
                messages.success(request, f"✅ PDF u ngarkua në Cloudinary")
            else:
                messages.error(request, f"❌ Problem me PDF: {result['error']}")

        # Thirr save() normal që do ekzekutojë logjikën e notification
        super().save_model(request, obj, form, change)

    def send_notification_active_books(self, request, queryset):
        """Dërgo notification vetëm për librat aktivë"""
        from notifications_api.services import send_book_notification

        sent = 0
        skipped = 0
        failed = 0

        for book in queryset:
            if not book.is_active:
                skipped += 1
                continue

            if book.notification_sent:
                skipped += 1
                continue

            try:
                success, response = send_book_notification(book)
                if success:
                    sent += 1
                else:
                    failed += 1
                    messages.warning(request, f'⚠️ {book.title}: {response}')
            except Exception as e:
                failed += 1
                messages.error(request, f'❌ Gabim për "{book.title}": {str(e)}')

        if sent > 0:
            messages.success(request, f'✅ U dërguan {sent} njoftime')
        if skipped > 0:
            messages.info(request, f'ℹ️ {skipped} libra u anashkaluan (jo aktivë ose njoftuar tashmë)')
        if failed > 0:
            messages.error(request, f'❌ {failed} njoftime dështuan')

    send_notification_active_books.short_description = "📨 Dërgo njoftim (vetëm për aktivë)"

    def send_notification_all_selected(self, request, queryset):
        """Dërgo notification për të gjithë të zgjedhurit (edhe nëse janë njoftuar më parë)"""
        from notifications_api.services import send_book_notification

        # Reset notification status
        queryset.update(notification_sent=False)

        sent = 0
        failed = 0

        for book in queryset:
            try:
                success, response = send_book_notification(book)
                if success:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                messages.error(request, f'❌ Gabim: {str(e)}')

        messages.success(request, f'✅ U dërguan {sent} njoftime (përfshirë ri-dërgime)')
        if failed > 0:
            messages.error(request, f'❌ {failed} dështuan')

    send_notification_all_selected.short_description = "📢 Dërgo njoftim për të gjithë (force)"

    def activate_and_notify(self, request, queryset):
        """Aktivizo librat dhe dërgo njoftim"""
        from notifications_api.services import send_book_notification

        # Aktivizo të gjithë
        activated = queryset.filter(is_active=False).update(is_active=True)

        # Dërgo njoftim
        sent = 0
        for book in queryset.filter(is_active=True, notification_sent=False):
            try:
                success, _ = send_book_notification(book)
                if success:
                    sent += 1
            except:
                pass

        messages.success(request, f'✅ U aktivizuan {activated} libra dhe u dërguan {sent} njoftime')

    activate_and_notify.short_description = "⚡ Aktivizo + Dërgo njoftim"

    def notification_status(self, obj):
        """Shfaq statusin e njoftimit me më shumë detaje"""
        if obj.notification_sent:
            times = obj.notification_count
            color = 'green' if times == 1 else 'blue'
            emoji = '✅' if times == 1 else '🔄'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} Dërguar ({}x)</span>',
                color, emoji, times
            )
        return format_html(
            '<span style="color: orange;">⏳ Jo ende</span>'
        )

    def reset_notification_status(self, request, queryset):
        """Reseto statusin e njoftimit (për testing)"""
        count = queryset.update(
            notification_sent=False,
            notification_sent_at=None,
            notification_count=0
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