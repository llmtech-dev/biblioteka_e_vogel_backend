from django.contrib import admin
from django.contrib import messages
from .models import Quiz, Question, AnswerOption
from notifications_api.services import send_quiz_notification
from notifications_api.models import Notification


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'book', 'created_at']
    list_filter = ['created_at', 'book__category']
    search_fields = ['title', 'book__title']
    inlines = [QuestionInline]
    readonly_fields = ['created_at']

    actions = ['send_notification_action']

    def send_notification_action(self, request, queryset):
        """Dërgon notifikim për kuizet e zgjedhur"""
        success_count = 0

        for quiz in queryset:
            success, response = send_quiz_notification(quiz)

            if success:
                Notification.objects.create(
                    title=f"Kuiz i ri: {quiz.title}",
                    description=f"Testo njohuritë për '{quiz.book.title}'",
                    type='newQuiz',
                    quiz=quiz,
                    book=quiz.book,
                )
                success_count += 1
            else:
                messages.error(request, f"Gabim për '{quiz.title}': {response}")

        if success_count > 0:
            messages.success(
                request,
                f"✅ U dërguan {success_count} njoftime me sukses!"
            )

    send_notification_action.short_description = "🎯 Dërgo njoftim për kuizin"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'correct_option_index']
    list_filter = ['quiz']
    inlines = [AnswerOptionInline]