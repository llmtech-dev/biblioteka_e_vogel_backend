from django.db import models
from books_api.models import Book


class Quiz(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_option_index = models.IntegerField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField()
    order = models.IntegerField()

    class Meta:
        ordering = ['order']