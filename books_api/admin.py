from django.contrib import admin
from django.contrib import messages
from .models import Book, BookPage, PageElement
from notifications_api.services import send_book_notification


class PageElementInline(admin.TabularInline):
    model = PageElement
    extra = 1


class BookPageInline(admin.TabularInline):
    model = BookPage
    extra = 1
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'author', 'translator']

    inlines = [BookPageInline]

    fieldsets = (
        ('Informacioni Bazë', {
            'fields': ('id', 'title', 'author', 'translator', 'category')
        }),
        ('Media', {
            'fields': ('cover_image', 'cover_file', 'pdf_path', 'pdf_file')
        }),
        ('Statusi', {
            'fields': ('is_active', 'version')
        })
    )

    actions = ['send_notification_for_books']

    def save_model(self, request, obj, form, change):
        """Dërgo notification kur shtohet libër i ri"""
        is_new = not change
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
        for book in queryset.filter(is_active=True):
            try:
                success, response = send_book_notification(book)
                if success:
                    sent += 1
            except:
                pass

        messages.success(request, f'✅ U dërguan {sent} njoftime për libra')

    send_notification_for_books.short_description = "Dërgo njoftim për librat e zgjedhur"