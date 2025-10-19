# quiz_api/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import Quiz, Question, AnswerOption
from notifications_api.services import send_quiz_notification


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4  # Për 4 opsione
    min_num = 2
    max_num = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ['text', 'correct_option_index', 'order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'book', 'get_question_count',
        'notification_sent', 'created_at'
    ]
    list_filter = ['notification_sent', 'created_at', 'book__category']
    search_fields = ['title', 'book__title']
    readonly_fields = [
        'id', 'notification_sent', 'notification_sent_at',
        'notification_count', 'created_at'
    ]

    inlines = [QuestionInline]

    fieldsets = (
        ('Quiz Info', {
            'fields': ('id', 'book', 'title')
        }),
        ('Notification Settings', {
            'fields': (
                'send_push_now',
                'notification_sent',
                'notification_sent_at',
                'notification_count'
            ),
            'classes': ('collapse',),
        }),
    )

    actions = ['send_notification_action', 'reset_notification_status']

    def get_question_count(self, obj):
        return obj.questions.count()

    get_question_count.short_description = 'Pyetje'

    def send_notification_action(self, request, queryset):
        """Manual notification send action"""
        sent_count = 0
        failed_count = 0

        for quiz in queryset:
            try:
                success, response = send_quiz_notification(quiz)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                self.message_user(
                    request,
                    f"Error sending notification for '{quiz.title}': {str(e)}",
                    level='ERROR'
                )

        if sent_count > 0:
            self.message_user(
                request,
                f"✅ {sent_count} quiz notification(s) sent successfully!"
            )

        if failed_count > 0:
            self.message_user(
                request,
                f"❌ {failed_count} notification(s) failed",
                level='WARNING'
            )

    send_notification_action.short_description = "📨 Dërgo push notification"

    def reset_notification_status(self, request, queryset):
        """Reset notification tracking"""
        updated = queryset.update(
            notification_sent=False,
            notification_sent_at=None,
            notification_count=0
        )
        self.message_user(
            request,
            f"🔄 Reset notification status for {updated} quiz(es)"
        )

    reset_notification_status.short_description = "🔄 Reset notification status"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['get_short_text', 'quiz', 'correct_option_index', 'order']
    list_filter = ['quiz__book__category']
    search_fields = ['text', 'quiz__title']
    ordering = ['quiz', 'order']

    inlines = [AnswerOptionInline]

    def get_short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    get_short_text.short_description = 'Pyetja'