# management/commands/test_notification.py
from django.core.management.base import BaseCommand
from notifications_api.services import send_notification_to_all


class Command(BaseCommand):
    def handle(self, *args, **options):
        success, response = send_notification_to_all(
            title="📚 Libër i ri për test!",
            body="Historia e Profetit Musa",
            data={
                'type': 'newBook',
                'book_id': 'test_123',
                'title': 'Historia e Profetit Musa',
                'author': 'Autor Test',
                'cover_image': 'https://example.com/book.jpg'
            }
        )

        if success:
            print(f"✅ Notification sent: {response}")
        else:
            print(f"❌ Error: {response}")