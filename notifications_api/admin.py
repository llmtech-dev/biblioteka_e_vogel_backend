from django.contrib import admin
from django.contrib import messages
from .models import Notification
from .services import send_notification_to_all, send_book_notification, send_quiz_notification
# from .services import send_multicast_notification, send_book_notification, send_quiz_notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'is_active', 'created_at', 'notification_sent_status']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'id']  # ✅ Shto id për debugging

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
            'fields': ('id', 'created_at'),  # ✅ Shto ID për debugging
            'classes': ('collapse',)
        })
    )

    actions = ['send_notification_now', 'activate_notifications', 'deactivate_notifications']

    def notification_sent_status(self, obj):
        """Shfaq statusin real të dërgimit"""
        # Kontrollo nëse është dërguar më parë bazuar në lidhjet
        if obj.type == 'newBook' and obj.book and obj.book.notification_sent:
            return "✅ Dërguar më: " + str(obj.book.notification_sent_at)
        elif obj.type == 'newQuiz' and obj.quiz and obj.quiz.notification_sent:
            return "✅ Dërguar më: " + str(obj.quiz.notification_sent_at)
        return "❌ Jo ende"

    notification_sent_status.short_description = "Statusi i dërgimit"

    def save_model(self, request, obj, form, change):
        """Override save për të dërguar notification automatikisht"""
        # Ruaj objektin fillimisht
        super().save_model(request, obj, form, change)

        # ✅ Dërgo notification për objekte të reja DHE kur kërkohet eksplicit
        should_send = (
                obj.is_active and
                (not change or request.POST.get('_send_notification', False))
        )

        if should_send:
            success = self._send_firebase_notification(obj, request)
            obj._notification_sent = success

    def _send_firebase_notification(self, notification, request):
        """Dërgon Firebase notification bazuar në tipin"""
        try:
            # Përgatit të dhënat bazuar në tipin
            if notification.type == 'newBook' and notification.book:
                success, response = send_book_notification(notification.book)

            elif notification.type == 'newQuiz' and notification.quiz:
                success, response = send_quiz_notification(notification.quiz)

            else:
                # ✅ Sigurohu që të gjitha të dhënat janë strings për Firebase
                data = {
                    'type': str(notification.type),
                    'notification_id': str(notification.id),
                    'title': str(notification.title),
                    'description': str(notification.description),
                }

                # Shto të dhëna specifike nëse ka
                if notification.book:
                    data.update({
                        'book_id': str(notification.book.id),
                        'book_title': str(notification.book.title),
                        'cover_image': str(notification.book.get_cover_url() or ''),
                    })
                elif notification.quiz:
                    data.update({
                        'quiz_id': str(notification.quiz.id),
                        'quiz_title': str(notification.quiz.title),
                        'book_id': str(notification.quiz.book.id),
                        'book_title': str(notification.quiz.book.title),
                    })

                if notification.image_url:
                    data['image_url'] = str(notification.image_url)

                # ✅ Debug
                self.stdout.write(f"Sending notification with data: {data}")

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
            import traceback
            messages.error(
                request,
                f'❌ Gabim në dërgimin e njoftimit: {str(e)}\n{traceback.format_exc()}'
            )
            return False