from django.contrib import admin
from django.contrib import messages
from .models import Book, BookPage, PageElement
from notifications_api.services import send_book_notification
from notifications_api.models import Notification


class PageElementInline(admin.TabularInline):
    model = PageElement
    extra = 1


class BookPageInline(admin.TabularInline):
    model = BookPage
    extra = 1
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'author']
    inlines = [BookPageInline]
    readonly_fields = ['created_at', 'updated_at']

    actions = ['send_notification_action']

    def send_notification_action(self, request, queryset):
        """Dërgon notifikim për librat e zgjedhur"""
        success_count = 0

        for book in queryset:
            # Dërgo notifikim me Firebase
            success, response = send_book_notification(book)

            if success:
                # Ruaj në database për tracking
                Notification.objects.create(
                    title=f"Libër i ri: {book.title}",
                    description=f"{book.title} nga {book.author} është gati për lexim!",
                    type='newBook',
                    book=book,
                    image_url=book.cover_image,
                )
                success_count += 1
            else:
                messages.error(request, f"Gabim për '{book.title}': {response}")

        if success_count > 0:
            messages.success(
                request,
                f"✅ U dërguan {success_count} njoftime me sukses!"
            )

    send_notification_action.short_description = "📱 Dërgo njoftim tek përdoruesit"

    # Override save për auto-notifikim (opsionale)
    def save_model(self, request, obj, form, change):
        is_new = obj._state.adding
        super().save_model(request, obj, form, change)

        # Nëse është libër i ri dhe është aktiv
        if is_new and obj.is_active:
            success, response = send_book_notification(obj)
            if success:
                messages.success(request, "✅ Njoftimi u dërgua automatikisht!")
                # Ruaj në database
                Notification.objects.create(
                    title=f"Libër i ri: {obj.title}",
                    description=f"{obj.title} nga {obj.author} është gati për lexim!",
                    type='newBook',
                    book=obj,
                    image_url=obj.cover_image,
                )


@admin.register(BookPage)
class BookPageAdmin(admin.ModelAdmin):
    list_display = ['book', 'page_number']
    list_filter = ['book']
    inlines = [PageElementInline]