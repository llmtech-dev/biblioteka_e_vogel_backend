from django.db import models
import uuid
from books_api.models import Book
from quizes_api.models import Quiz


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('newBook', 'New Book'),
        ('newQuiz', 'New Quiz'),
        ('update', 'Update'),
        ('announcement', 'Announcement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Për të kontrolluar cilat njoftime janë aktive

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title