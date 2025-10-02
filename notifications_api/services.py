import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import json

# Initialize Firebase Admin SDK
cred_path = settings.BASE_DIR / 'firebase-credentials.json'
if cred_path.exists():
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


def send_notification_to_all(title, body, data=None):
    """Dërgon notifikim tek të gjithë përdoruesit"""
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        topic='all_users',  # Të gjithë përdoruesit duhet të subscribe këtu
    )

    try:
        response = messaging.send(message)
        return True, response
    except Exception as e:
        return False, str(e)


def send_book_notification(book):
    """Dërgon notifikim për libër të ri"""
    title = "📚 Libër i ri!"
    body = f"{book.title} nga {book.author}"

    data = {
        'type': 'newBook',
        'book_id': str(book.id),
        'title': book.title,
        'author': book.author,
        'category': book.category,
        'cover_image': book.cover_image,
    }

    return send_notification_to_all(title, body, data)


def send_quiz_notification(quiz):
    """Dërgon notifikim për kuiz të ri"""
    title = "🎯 Kuiz i ri!"
    body = f"{quiz.title} për librin {quiz.book.title}"

    data = {
        'type': 'newQuiz',
        'quiz_id': str(quiz.id),
        'book_id': str(quiz.book.id),
        'title': quiz.title,
    }

    return send_notification_to_all(title, body, data)