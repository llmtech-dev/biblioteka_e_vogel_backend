from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from .models import Quiz, Question, AnswerOption
from notifications_api.services import send_quiz_notification


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4
    fields = ['text', 'order']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['text', 'correct_option_index', 'order']
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'book',
        'question_count',
        'notification_status',
        'notification_sent_at',
        'notification_count',
        'created_at'
    ]
    list_filter = [
        'notification_sent',
        'created_at',
        'book__category',
        'notification_sent_at'
    ]
    search_fields = ['title', 'book__title', 'id']
    inlines = [QuestionInline]
    readonly_fields = [
        'id',
        'created_at',
        'notification_sent',
        'notification_sent_at',
        'notification_count'
    ]

    fieldsets = (
        ('Informacioni Bazë', {
            'fields': ('title', 'book')
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
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['send_notification_for_quizzes', 'reset_notification_status']

    def question_count(self, obj):
        """Shfaq numrin e pyetjeve"""
        count = obj.questions.count()
        return format_html(
            '<span style="color: {};">{} pyetje</span>',
            'green' if count > 0 else 'red',
            count
        )

    question_count.short_description = '📝 Pyetje'

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
                        f'✅ Kuizi u ruajt dhe njoftimi u dërgua! Response: {response}'
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
        already_sent = 0

        for quiz in queryset:
            # Kontrollo nëse është dërguar tashmë
            if quiz.notification_sent:
                already_sent += 1
                continue

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

        # Mesazhet përfundimtare
        if sent > 0:
            messages.success(request, f'✅ U dërguan {sent} njoftime të reja')
        if already_sent > 0:
            messages.info(request, f'ℹ️ {already_sent} kuize kishin njoftim të dërguar tashmë')
        if failed > 0:
            messages.error(request, f'❌ {failed} njoftime dështuan')

    send_notification_for_quizzes.short_description = "🎯 Dërgo njoftim për kuizet e zgjedhur"

    def reset_notification_status(self, request, queryset):
        """Reseto statusin e njoftimit (për testing)"""
        count = queryset.update(
            notification_sent=False,
            notification_sent_at=None
        )
        messages.success(request, f'🔄 U resetua statusi për {count} kuize')

    reset_notification_status.short_description = "🔄 Reseto statusin e njoftimeve"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'quiz', 'correct_option_index', 'order', 'option_count']
    list_filter = ['quiz', 'quiz__book__category']
    search_fields = ['text', 'quiz__title', 'id']
    inlines = [AnswerOptionInline]
    ordering = ['quiz', 'order']

    def short_text(self, obj):
        """Shfaq versionin e shkurtër të pyetjes"""
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text

    short_text.short_description = 'Pyetja'

    def option_count(self, obj):
        """Numri i opsioneve"""
        count = obj.options.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count >= 2 else 'red',
            count
        )

    option_count.short_description = 'Opsione'


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'question_quiz', 'order', 'is_correct']
    list_filter = ['question__quiz']
    search_fields = ['text', 'question__text']

    def short_text(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text

    short_text.short_description = 'Teksti'

    def question_quiz(self, obj):
        return f"{obj.question.quiz.title}"

    question_quiz.short_description = 'Kuizi'

    def is_correct(self, obj):
        if obj.question.options.all()[obj.question.correct_option_index].id == obj.id:
            return format_html('<span style="color: green;">✓ Po</span>')
        return format_html('<span style="color: gray;">✗ Jo</span>')

    is_correct.short_description = 'Përgjigje e saktë?'