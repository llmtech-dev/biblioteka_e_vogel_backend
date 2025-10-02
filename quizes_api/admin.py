from django.contrib import admin
from .models import Quiz, Question, AnswerOption


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


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'correct_option_index']
    list_filter = ['quiz']
    inlines = [AnswerOptionInline]