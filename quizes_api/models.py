from django.db import models
import uuid
from books_api.models import Book


class Quiz(models.Model):
    # ✅ UUID automatik
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    send_push_now = models.BooleanField(
        default=False,
        verbose_name='Dërgo njoftim',
        help_text='✓ Shëno për të dërguar push notification kur ruhet kuizi'
    )

    # Tracking
    notification_sent = models.BooleanField(default=False, verbose_name='Njoftimi u dërgua')
    notification_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Dërguar më')
    notification_count = models.IntegerField(default=0, verbose_name='Nr. njoftimesh')

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Save me logjikë për notification"""
        is_new = self.pk is None
        should_send_push = self.send_push_now

        # Reset send_push_now
        if should_send_push:
            self.send_push_now = False

        # Save normal
        super().save(*args, **kwargs)

        # Send notification nëse u kërkua
        if should_send_push and self.pk:
            from django.db import transaction

            def send_notification():
                from notifications_api.services import send_quiz_notification
                send_quiz_notification(self)

            transaction.on_commit(send_notification)


class Question(models.Model):
    # ✅ UUID automatik
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_option_index = models.IntegerField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:50]}..."


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField()
    order = models.IntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text[:30]