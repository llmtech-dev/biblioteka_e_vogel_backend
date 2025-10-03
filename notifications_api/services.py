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
    """
    Dërgon notification për kuiz të ri
    """
    question_count = quiz.questions.count()

    data = {
        'type': 'newQuiz',
        'quiz_id': str(quiz.id),
        'quiz_title': quiz.title,
        'book_id': str(quiz.book.id),
        'book_title': quiz.book.title,
        'category': quiz.book.category,
        'question_count': str(question_count),
    }

    # Shto cover image të librit nëse ekziston
    if quiz.book.cover_image:
        data['cover_image'] = quiz.book.cover_image

    return send_notification_to_all(
        title=f"🎯 Kuiz i ri: {quiz.title}",
        body=f"Testo njohuritë për '{quiz.book.title}' - {question_count} pyetje",
        data=data
    )