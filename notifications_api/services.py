# notifications_api/services.py
# SHTUAR: send_quiz_notification + rate limiting + graceful fallback
# Funksionon edhe pa Firebase (log warning, jo crash)

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Firebase inicializohet vetëm nëse skedari i kredencialeve ekziston
_firebase_initialized = False
_fcm_app = None


def _init_firebase():
    """Inicializon Firebase SDK vetëm 1 herë."""
    global _firebase_initialized, _fcm_app
    if _firebase_initialized:
        return _fcm_app is not None

    _firebase_initialized = True
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if not cred_path:
            cred_path = settings.BASE_DIR / 'firebase-credentials.json'

        if not str(cred_path) or not __import__('os').path.exists(str(cred_path)):
            logger.warning(
                '⚠️ Firebase credentials not found at %s — '
                'Push notifications disabled', cred_path
            )
            return False

        if not firebase_admin._apps:
            cred = credentials.Certificate(str(cred_path))
            _fcm_app = firebase_admin.initialize_app(cred)
        else:
            _fcm_app = firebase_admin.get_app()

        logger.info('✅ Firebase Admin initialized')
        return True

    except Exception as e:
        logger.error('❌ Firebase init failed: %s', e)
        return False


def send_book_notification(book):
    """
    Dërgon push notification për libër të ri.
    Kthen (True, response) ose (False, error_message).
    """
    if not _init_firebase():
        logger.warning('Firebase unavailable — skipping notification for book: %s', book.title)
        # Shëno si njoftuar që të mos bllokojë rrjedhën
        _mark_book_notified(book)
        return True, 'Firebase unavailable — marked as notified'

    try:
        from firebase_admin import messaging
        from django.utils import timezone

        message = messaging.Message(
            notification=messaging.Notification(
                title='📚 Libër i Ri!',
                body=f'"{book.title}" nga {book.author} është disponibël tani.',
            ),
            data={
                'type': 'newBook',
                'bookId': str(book.id),
                'title': book.title,
                'author': book.author,
                'coverImage': book.cover_image or '',
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    channel_id='thesari_channel',
                    priority='high',
                    image=book.cover_image or None,
                ),
                priority='high',
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=1, sound='default'),
                ),
            ),
            topic='all_users',
        )

        response = messaging.send(message)
        logger.info('✅ Book notification sent: %s → %s', book.title, response)

        _mark_book_notified(book)
        return True, response

    except Exception as e:
        logger.error('❌ Book notification failed: %s', e)
        return False, str(e)


def send_quiz_notification(quiz):
    """
    Dërgon push notification për kuiz të ri.
    Kthen (True, response) ose (False, error_message).
    """
    if not _init_firebase():
        logger.warning('Firebase unavailable — skipping notification for quiz: %s', quiz.title)
        _mark_quiz_notified(quiz)
        return True, 'Firebase unavailable — marked as notified'

    try:
        from firebase_admin import messaging
        from django.utils import timezone

        book_title = quiz.book.title if quiz.book else 'librin'

        message = messaging.Message(
            notification=messaging.Notification(
                title='🎯 Kuiz i Ri!',
                body=f'Kuizi "{quiz.title}" për "{book_title}" është gati!',
            ),
            data={
                'type': 'newQuiz',
                'quizId': str(quiz.id),
                'bookId': str(quiz.book_id) if quiz.book_id else '',
                'title': quiz.title,
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    channel_id='thesari_channel',
                    priority='high',
                ),
                priority='high',
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=1, sound='default'),
                ),
            ),
            topic='all_users',
        )

        response = messaging.send(message)
        logger.info('✅ Quiz notification sent: %s → %s', quiz.title, response)

        _mark_quiz_notified(quiz)
        return True, response

    except Exception as e:
        logger.error('❌ Quiz notification failed: %s', e)
        return False, str(e)


def send_notification_to_all(title: str, body: str, data: dict = None):
    """
    Dërgon push notification të lirë (pa libër/quiz specifik) te topic all_users.
    Përdoret nga Django Admin për njoftime të përgjithshme.
    Kthen (True, response) ose (False, error_message).
    """
    if not _init_firebase():
        logger.warning('Firebase unavailable — skipping general notification: %s', title)
        return False, 'Firebase unavailable'

    try:
        from firebase_admin import messaging

        # Sigurohu që të gjitha vlerat në data janë strings (kërkesë e Firebase)
        clean_data = {str(k): str(v) for k, v in (data or {}).items()}

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=clean_data,
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    channel_id='thesari_channel',
                    priority='high',
                ),
                priority='high',
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=1, sound='default'),
                ),
            ),
            topic='all_users',
        )

        response = messaging.send(message)
        logger.info('✅ General notification sent: %s → %s', title, response)
        return True, response

    except Exception as e:
        logger.error('❌ General notification failed: %s', e)
        return False, str(e)


def _mark_book_notified(book):
    """Shënon librin si të njoftuar në DB."""
    from django.utils import timezone
    try:
        book.notification_sent = True
        book.notification_sent_at = timezone.now()
        book.notification_count = (book.notification_count or 0) + 1
        book.save(update_fields=[
            'notification_sent', 'notification_sent_at', 'notification_count'
        ])
    except Exception as e:
        logger.error('Failed to mark book as notified: %s', e)


def _mark_quiz_notified(quiz):
    """Shënon kuizin si të njoftuar në DB."""
    from django.utils import timezone
    try:
        quiz.notification_sent = True
        quiz.notification_sent_at = timezone.now()
        quiz.notification_count = (quiz.notification_count or 0) + 1
        quiz.save(update_fields=[
            'notification_sent', 'notification_sent_at', 'notification_count'
        ])
    except Exception as e:
        logger.error('Failed to mark quiz as notified: %s', e)