import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
import json

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


import logging

logger = logging.getLogger(__name__)


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
        print(f"✅ Firebase SUCCESS: {response}")  # ✅ Print në console
        return True, response
    except Exception as e:
        logger.error(f"Firebase error: {str(e)}")
        print(f"❌ Firebase ERROR: {str(e)}")  # ✅ Print në console
        import traceback
        traceback.print_exc()  # ✅ Print full error
        return False, str(e)


def send_book_notification(book):
    """Dërgon notifikim për libër të ri dhe e track"""
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

    success, response = send_notification_to_all(title, body, data)

    # ✅ Track notification
    if success:
        book.notification_sent = True
        book.notification_sent_at = timezone.now()
        book.notification_count += 1
        book.save(update_fields=['notification_sent', 'notification_sent_at', 'notification_count'])

    return success, response


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



#
# from django.utils import timezone
# from firebase_admin import messaging
# import firebase_admin
# from firebase_admin import credentials
# from django.conf import settings
# import os
# import json
#
# # Initialize Firebase Admin SDK
# if not firebase_admin._apps:
#     # Merr credentials nga settings ose environment
#     cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
#
#     if cred_path and os.path.exists(cred_path):
#         cred = credentials.Certificate(cred_path)
#     else:
#         # Ose përdor nga settings nëse e ke si JSON string
#         firebase_config = getattr(settings, 'FIREBASE_ADMIN_CREDENTIALS', None)
#         if firebase_config:
#             cred = credentials.Certificate(json.loads(firebase_config))
#         else:
#             # Default path
#             cred = credentials.Certificate('firebase-credentials.json')
#
#     firebase_admin.initialize_app(cred)
#
#
# def send_book_notification(book):
#     """
#     Dërgon push notification për një libër të ri
#     Returns: (success: bool, message: str)
#     """
#     try:
#         # Skip nëse është dërguar më parë
#         if book.notification_sent:
#             return False, "Njoftimi është dërguar më parë"
#
#         # Përgatit të dhënat e njoftimit
#         notification_data = {
#             'type': 'new_book',
#             'book_id': str(book.id),
#             'book_title': book.title,
#             'book_author': book.author,
#             'book_category': book.category,
#             'cover_url': book.get_cover_url() or '',
#             'pdf_url': book.pdf_path or '',
#             'timestamp': str(timezone.now().timestamp()),
#         }
#
#         # Krijo mesazhin për Firebase
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title='📚 Libër i ri në bibliotekë!',
#                 body=f'"{book.title}" nga {book.author}',
#                 image=book.get_cover_url() if book.get_cover_url() else None,
#             ),
#             data=notification_data,
#             android=messaging.AndroidConfig(
#                 priority='high',
#                 notification=messaging.AndroidNotification(
#                     icon='book_icon',
#                     color='#1976D2',
#                     sound='default',
#                     tag='new_book',
#                     click_action='FLUTTER_NOTIFICATION_CLICK',
#                 ),
#             ),
#             apns=messaging.APNSConfig(
#                 payload=messaging.APNSPayload(
#                     aps=messaging.Aps(
#                         alert=messaging.ApsAlert(
#                             title='📚 Libër i ri në bibliotekë!',
#                             body=f'"{book.title}" nga {book.author}',
#                         ),
#                         sound='default',
#                         badge=1,
#                     ),
#                 ),
#             ),
#             topic='new_books',  # Dërgo te të gjithë që janë subscribe
#         )
#
#         # Dërgo mesazhin
#         response = messaging.send(message)
#
#         # Update book notification status
#         book.notification_sent = True
#         book.notification_sent_at = timezone.now()
#         book.notification_count = book.notification_count + 1
#         book.save(update_fields=['notification_sent', 'notification_sent_at', 'notification_count'])
#
#         return True, f"Message ID: {response}"
#
#     except Exception as e:
#         return False, str(e)
#
#
# def send_quiz_notification(quiz):
#     """
#     Dërgon notification për quiz të ri
#     """
#     try:
#         notification_data = {
#             'type': 'new_quiz',
#             'quiz_id': str(quiz.id),
#             'quiz_title': quiz.title,
#             'quiz_book_id': str(quiz.book.id) if quiz.book else '',
#             'quiz_book_title': quiz.book.title if quiz.book else '',
#             'question_count': str(quiz.questions.count()),
#             'timestamp': str(timezone.now().timestamp()),
#         }
#
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title='🎯 Kuiz i ri!',
#                 body=f'{quiz.title} - {quiz.questions.count()} pyetje',
#             ),
#             data=notification_data,
#             topic='new_quizzes',
#         )
#
#         response = messaging.send(message)
#         return True, f"Message ID: {response}"
#
#     except Exception as e:
#         return False, str(e)
#
#
# def send_custom_notification(title, body, data=None, topic='general'):
#     """
#     Dërgon notification të personalizuar
#     """
#     try:
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title=title,
#                 body=body,
#             ),
#             data=data or {},
#             topic=topic,
#         )
#
#         response = messaging.send(message)
#         return True, f"Message ID: {response}"
#
#     except Exception as e:
#         return False, str(e)
#
#
# def send_multicast_notification(title, body, tokens):
#     """
#     Dërgon notification te disa përdorues specifik
#     """
#     try:
#         message = messaging.MulticastMessage(
#             notification=messaging.Notification(
#                 title=title,
#                 body=body,
#             ),
#             tokens=tokens,
#         )
#
#         response = messaging.send_multicast(message)
#         return True, f"Successfully sent: {response.success_count}"
#
#     except Exception as e:
#         return False, str(e)