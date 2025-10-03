from django.contrib import admin
from django.contrib import messages
from .models import Notification
from .services import send_notification_to_all, send_book_notification, send_quiz_notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'is_active', 'created_at', 'notification_sent']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']

    # Shto field për të trackuar nëse është dërguar
    fieldsets = (
        ('Përmbajtja', {
            'fields': ('title', 'description', 'type', 'image_url')
        }),
        ('Lidhjet', {
            'fields': ('book', 'quiz'),
            'description': 'Zgjidh librin OSE kuizin (jo të dyja)'
        }),
        ('Statusi', {
            'fields': ('is_active',)
        }),
        ('Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    actions = ['send_notification_now', 'activate_notifications', 'deactivate_notifications']

    def notification_sent(self, obj):
        """Shfaq nëse notification është dërguar"""
        return "✅ Po" if hasattr(obj, '_notification_sent') else "❌ Jo"

    notification_sent.short_description = "Dërguar?"

    def save_model(self, request, obj, form, change):
        """Override save për të dërguar notification automatikisht"""
        # Ruaj objektin fillimisht
        super().save_model(request, obj, form, change)

        # Dërgo notification vetëm nëse është aktiv dhe i ri (jo update)
        if obj.is_active and not change:
            success = self._send_firebase_notification(obj, request)
            obj._notification_sent = success

    def _send_firebase_notification(self, notification, request):
        """Dërgon Firebase notification bazuar në tipin"""
        try:
            # Përgatit të dhënat bazuar në tipin
            if notification.type == 'newBook' and notification.book:
                # Përdor metodën ekzistuese për libër
                success, response = send_book_notification(notification.book)

            elif notification.type == 'newQuiz' and notification.quiz:
                # Përdor metodën ekzistuese për kuiz
                success, response = send_quiz_notification(notification.quiz)

            else:
                # Notification i përgjithshëm
                data = {
                    'type': notification.type,
                    'notification_id': str(notification.id),
                    'title': notification.title,
                    'description': notification.description,
                }

                # Shto të dhëna specifike nëse ka
                if notification.book:
                    data.update({
                        'book_id': str(notification.book.id),
                        'book_title': notification.book.title,
                        'cover_image': notification.book.cover_image,
                    })
                elif notification.quiz:
                    data.update({
                        'quiz_id': str(notification.quiz.id),
                        'quiz_title': notification.quiz.title,
                    })

                if notification.image_url:
                    data['image_url'] = notification.image_url

                success, response = send_notification_to_all(
                    title=notification.title,
                    body=notification.description,
                    data=data
                )

            if success:
                messages.success(
                    request,
                    f'✅ Njoftimi u dërgua me sukses! Response: {response}'
                )
                return True
            else:
                messages.error(
                    request,
                    f'❌ Gabim në dërgimin e njoftimit: {response}'
                )
                return False

        except Exception as e:
            messages.error(
                request,
                f'❌ Gabim në dërgimin e njoftimit: {str(e)}'
            )
            return False

    def send_notification_now(self, request, queryset):
        """Action për të dërguar notification manualisht"""
        sent_count = 0
        error_count = 0

        for notification in queryset:
            if notification.is_active:
                if self._send_firebase_notification(notification, request):
                    sent_count += 1
                else:
                    error_count += 1
            else:
                messages.warning(
                    request,
                    f'⚠️ Njoftimi "{notification.title}" nuk është aktiv'
                )

        if sent_count > 0:
            messages.success(
                request,
                f'✅ U dërguan {sent_count} njoftime me sukses'
            )
        if error_count > 0:
            messages.error(
                request,
                f'❌ {error_count} njoftime nuk u dërguan'
            )

    send_notification_now.short_description = "Dërgo njoftimet e zgjedhura tani"

    def activate_notifications(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} njoftime u aktivizuan")

    activate_notifications.short_description = "Aktivizo njoftimet e zgjedhura"

    def deactivate_notifications(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} njoftime u çaktivizuan")

    deactivate_notifications.short_description = "Çaktivizo njoftimet e zgjedhura"