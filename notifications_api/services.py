import firebase_admin
from django.db import models
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
import json
import logging
logger = logging.getLogger(__name__)

from books_api.models import Book

# Initialize Firebase Admin SDK
cred_path = settings.BASE_DIR / 'firebase-credentials.json'
if cred_path.exists():
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


# def send_notification_to_all(title, body, data=None):
#     """Dërgon notifikim tek të gjithë përdoruesit"""
#     message = messaging.Message(
#         notification=messaging.Notification(
#             title=title,
#             body=body,
#         ),
#         data=data or {},
#         topic='all_users',
#     )
#
#     try:
#         response = messaging.send(message)
#         return True, response
#     except Exception as e:
#         return False, str(e)


def send_notification_to_all(title, body, data=None):
    """Dërgon notifikim tek të gjithë përdoruesit"""
    # ✅ Konverto të gjitha values në strings
    if data:
        data = {k: str(v) for k, v in data.items() if v is not None}

    logger.info(f"Sending notification - Title: {title}, Body: {body}, Data: {data}")

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        topic='all_users',
    )

    try:
        response = messaging.send(message)
        logger.info(f"Firebase response: {response}")
        print(f"✅ Firebase SUCCESS: {response}")
        return True, response
    except Exception as e:
        logger.error(f"Firebase error: {str(e)}")
        print(f"❌ Firebase ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e)


# notifications_api/services.py

def send_book_notification(book):
    """Dërgon notifikim për libër të ri dhe e track"""

    # # Prevent duplicate notifications
    # if book.notification_sent:
    #     logger.warning(f"Notification already sent for book {book.id}")
    #     return False, "Notification already sent"

    title = "📚 Libër i ri!"
    body = f"{book.title} nga {book.author}"

    # Get absolute URLs
    cover_url = book.get_cover_url()
    pdf_url = ''

    # Handle PDF URL
    if book.pdf_path and book.pdf_path.startswith('http'):
        pdf_url = book.pdf_path
    elif book.pdf_file:
        try:
            # Get absolute URL for local files
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            domain = f"https://{current_site.domain}"

            # For local development
            if 'localhost' in domain or '127.0.0.1' in domain:
                domain = "http://127.0.0.1:8000"

            pdf_url = f"{domain}{book.pdf_file.url}"
        except Exception as e:
            logger.error(f"Error getting PDF URL: {e}")
            pdf_url = book.pdf_file.url if book.pdf_file else ''

    # Build notification data - VETËM METADATA, JO PAGES!
    data = {
        'type': 'newBook',
        'book_id': str(book.id),
        'title': book.title,
        'author': book.author,
        'category': book.category,
        'cover_url': cover_url or '',
        'pdf_url': pdf_url or '',
        'timestamp': timezone.now().isoformat(),
        # SHTO page count për info
        'page_count': str(book.pages.count()),
        'has_pdf': 'true' if pdf_url else 'false',
    }

    # Log for debugging
    logger.info(f"📨 Sending notification for book: {book.title}")
    logger.info(f"📊 Notification data: {json.dumps(data, indent=2)}")

    success, response = send_notification_to_all(title, body, data)

    if success:
        # Update book notification status
        Book.objects.filter(pk=book.pk).update(
            notification_sent=True,
            notification_sent_at=timezone.now(),
            notification_count=models.F('notification_count') + 1,
            send_push_now=False
        )
        logger.info(f"✅ Notification sent successfully for book {book.id}")
    else:
        logger.error(f"❌ Failed to send notification: {response}")

    return success, response


# notifications_api/services.py

def send_book_update_notification(book, old_instance=None):
    """Dërgon notifikim për libër të përditësuar"""

    # Prevent spam - check last notification time
    if book.notification_sent_at:
        time_since_last = timezone.now() - book.notification_sent_at
        if time_since_last.total_seconds() < 300:  # 5 minuta
            logger.warning(f"Skipping update notification - too soon since last one")
            return False, "Too soon since last notification"

    title = "📚 Libër i përditësuar!"

    # Check what changed
    changes = []
    if old_instance:
        if book.title != old_instance.title:
            changes.append("titull i ri")
        if book.author != old_instance.author:
            changes.append("autor i përditësuar")
        if book.cover_image != old_instance.cover_image or book.cover_file != old_instance.cover_file:
            changes.append("kopertinë e re")
        if book.pdf_path != old_instance.pdf_path or book.pdf_file != old_instance.pdf_file:
            changes.append("PDF i përditësuar")
        if book.category != old_instance.category:
            changes.append("kategori e re")

    # Build body message
    body = f"{book.title} nga {book.author}"
    if changes:
        body += f" - Ndryshime: {', '.join(changes)}"
    else:
        body += " - Përmbajtje e përditësuar"

    # Get URLs
    cover_url = book.get_cover_url()
    pdf_url = ''

    if book.pdf_path and book.pdf_path.startswith('http'):
        pdf_url = book.pdf_path
    elif book.pdf_file:
        try:
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            domain = f"https://{current_site.domain}"

            if 'localhost' in domain or '127.0.0.1' in domain:
                domain = "http://127.0.0.1:8000"

            pdf_url = f"{domain}{book.pdf_file.url}"
        except Exception as e:
            logger.error(f"Error getting PDF URL: {e}")
            pdf_url = book.pdf_file.url if book.pdf_file else ''

    # Build notification data
    data = {
        'type': 'bookUpdate',
        'book_id': str(book.id),
        'title': book.title,
        'author': book.author,
        'category': book.category,
        'cover_url': cover_url or '',
        'pdf_url': pdf_url or '',
        'timestamp': timezone.now().isoformat(),
        'update_type': 'content_update',
        'page_count': str(book.pages.count()),
        'version': str(book.version),
    }

    logger.info(f"📘 Sending UPDATE notification for book: {book.title}")
    logger.info(f"📊 Changes: {changes if changes else 'General update'}")
    logger.info(f"📊 Notification data: {json.dumps(data, indent=2)}")

    success, response = send_notification_to_all(title, body, data)

    if success:
        # Update book notification tracking
        Book.objects.filter(pk=book.pk).update(
            notification_sent=True,  # Keep as True
            notification_sent_at=timezone.now(),
            notification_count=models.F('notification_count') + 1,
            version=models.F('version') + 1,  # Increment version
        )
        logger.info(f"✅ Update notification sent for book {book.id}")
    else:
        logger.error(f"❌ Failed to send update notification: {response}")

    return success, response


# def send_book_notification(book):
#     """Dërgon notifikim për libër të ri dhe e track"""
#
#     # Prevent duplicate notifications
#     if book.notification_sent:
#         logger.warning(f"Notification already sent for book {book.id}")
#         return False, "Notification already sent"
#
#     title = "📚 Libër i ri!"
#     body = f"{book.title} nga {book.author}"
#
#     # Get absolute URLs
#     cover_url = book.get_cover_url()
#     pdf_url = ''
#
#     # Handle PDF URL
#     if book.pdf_path and book.pdf_path.startswith('http'):
#         pdf_url = book.pdf_path
#     elif book.pdf_file:
#         try:
#             # Get absolute URL for local files
#             from django.contrib.sites.models import Site
#             current_site = Site.objects.get_current()
#             domain = f"https://{current_site.domain}"
#
#             # For local development
#             if 'localhost' in domain or '127.0.0.1' in domain:
#                 domain = "http://127.0.0.1:8000"
#
#             pdf_url = f"{domain}{book.pdf_file.url}"
#         except Exception as e:
#             logger.error(f"Error getting PDF URL: {e}")
#             pdf_url = book.pdf_file.url if book.pdf_file else ''
#
#     # Build notification data
#     data = {
#         'type': 'newBook',
#         'book_id': str(book.id),
#         'title': book.title,
#         'author': book.author,
#         'category': book.category,
#         'cover_url': cover_url or '',
#         'pdf_url': pdf_url or '',
#         'timestamp': timezone.now().isoformat(),
#     }
#
#     # Log for debugging
#     logger.info(f"📨 Sending notification for book: {book.title}")
#     logger.info(f"📊 Notification data: {json.dumps(data, indent=2)}")
#
#     success, response = send_notification_to_all(title, body, data)
#
#     if success:
#         # Update book notification status
#         Book.objects.filter(pk=book.pk).update(
#             notification_sent=True,
#             notification_sent_at=timezone.now(),
#             notification_count=models.F('notification_count') + 1,
#             send_push_now=False
#         )
#         logger.info(f"✅ Notification sent successfully for book {book.id}")
#     else:
#         logger.error(f"❌ Failed to send notification: {response}")
#
#     return success, response


def send_quiz_notification(quiz):
    """Dërgon notifikim për kuiz të ri dhe e track"""
    question_count = quiz.questions.count()

    title = "🎯 Kuiz i ri!"
    body = f"{quiz.title} - {question_count} pyetje për '{quiz.book.title}'"

    data = {
        'type': 'newQuiz',
        'quiz_id': str(quiz.id),
        'book_id': str(quiz.book.id),
        'quiz_title': quiz.title,
        'book_title': quiz.book.title,
        'question_count': str(question_count),
        'category': str(quiz.book.category),
    }

    # Shto cover image nëse ka
    if quiz.book.cover_image:
        data['cover_image'] = quiz.book.cover_image

    success, response = send_notification_to_all(title, body, data)

    # ✅ Track notification
    if success:
        quiz.notification_sent = True
        quiz.notification_sent_at = timezone.now()
        quiz.notification_count += 1
        quiz.save(update_fields=['notification_sent', 'notification_sent_at', 'notification_count'])

    return success, response
