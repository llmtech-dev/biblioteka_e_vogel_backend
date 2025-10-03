from django.contrib import admin
from django.contrib import messages
from .models import Quiz, Question, AnswerOption
from notifications_api.services import send_quiz_notification


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'book', 'created_at', 'question_count']
    list_filter = ['created_at', 'book__category']
    search_fields = ['title', 'book__title']
    inlines = [QuestionInline]
    readonly_fields = ['created_at']

    actions = ['send_notification_for_quizzes']

    def question_count(self, obj):
        """Shfaq numrin e pyetjeve"""
        return obj.questions.count()

    question_count.short_description = 'Pyetje'

    def save_model(self, request, obj, form, change):
        """Dërgo notification kur shtohet kuiz i ri"""
        is_new = not change
        super().save_model(request, obj, form, change)

        # Dërgo notification vetëm për kuize të rinj
        if is_new:
            try:
                success, response = send_quiz_notification(obj)
                if success:
                    messages.success(
                        request,
                        f'✅ Njoftimi për kuizin u dërgua: {response}'
                    )
                else:
                    messages.warning(
                        request,
                        f'⚠️ Kuizi u ruajt por njoftimi nuk u dërgua: {response}'
                    )
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Gabim në dërgimin e njoftimit: {str(e)}'
                )

    def send_notification_for_quizzes(self, request, queryset):
        """Dërgo notification për kuizet e zgjedhur"""
        sent = 0
        failed = 0

        for quiz in queryset:
            try:
                success, response = send_quiz_notification(quiz)
                if success:
                    sent += 1
                else:
                    failed += 1
                    messages.warning(
                        request,
                        f'⚠️ Kuizi "{quiz.title}": {response}'
                    )
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f'❌ Gabim për "{quiz.title}": {str(e)}'
                )

        if sent > 0:
            messages.success(request, f'✅ U dërguan {sent} njoftime për kuize')
        if failed > 0:
            messages.error(request, f'❌ {failed} njoftime dështuan')

    send_notification_for_quizzes.short_description = "🎯 Dërgo njoftim për kuizet e zgjedhur"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'quiz', 'correct_option_index', 'order']
    list_filter = ['quiz']
    search_fields = ['text', 'quiz__title']
    inlines = [AnswerOptionInline]
    ordering = ['quiz', 'order']

    def short_text(self, obj):
        """Shfaq versionin e shkurtër të pyetjes"""
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text

    short_text.short_description = 'Pyetja'