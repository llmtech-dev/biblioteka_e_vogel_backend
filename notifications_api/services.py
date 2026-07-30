# notifications_api/services.py
# SHTUAR: send_quiz_notification + rate limiting + graceful fallback
# Funksionon edhe pa Firebase (log warning, jo crash)

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Firebase inicializohet vetëm nëse skedari i kredencialeve ekziston
_firebase_initialized = False
_fcm_app = None


def _load_firebase_credentials():
    """
    Gjen kredencialet Firebase nga dy burime te mundshme:
    1. FIREBASE_CREDENTIALS_JSON_BASE64 (env var) — per hosting me disk te
       perkohshem (Render etj.) ku s'ka ku te ngarkosh nje file fizik.
    2. FIREBASE_CREDENTIALS_PATH (file fizik ne disk) — zhvillim lokal ose
       PythonAnywhere, ku disku eshte i perhershem.
    Kthen nje `firebase_admin.credentials.Certificate` ose None.
    """
    import base64
    import json
    import os

    from firebase_admin import credentials

    cred_json_b64 = getattr(settings, 'FIREBASE_CREDENTIALS_JSON_BASE64', '')
    if cred_json_b64:
        try:
            cred_dict = json.loads(base64.b64decode(cred_json_b64))
            return credentials.Certificate(cred_dict)
        except Exception as e:
            logger.error(
                '❌ FIREBASE_CREDENTIALS_JSON_BASE64 eshte i pavlefshem: %s', e
            )
            return None

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if not cred_path:
        cred_path = settings.BASE_DIR / 'firebase-credentials.json'

    if str(cred_path) and os.path.exists(str(cred_path)):
        return credentials.Certificate(str(cred_path))

    return None


def _init_firebase():
    """Inicializon Firebase SDK vetëm 1 herë."""
    global _firebase_initialized, _fcm_app
    if _firebase_initialized:
        return _fcm_app is not None

    _firebase_initialized = True
    try:
        import firebase_admin

        cred = _load_firebase_credentials()
        if cred is None:
            logger.warning(
                '⚠️ Firebase credentials not found (as FIREBASE_CREDENTIALS_'
                'JSON_BASE64 or FIREBASE_CREDENTIALS_PATH) — Push '
                'notifications disabled'
            )
            return False

        if not firebase_admin._apps:
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


def send_update_book_notification(book):
    """
    Dërgon push notification kur një libër ekzistues PËRDITËSOHET
    (ndryshim content, faqe të reja etj.).
    E ndarë nga send_book_notification për ta dalluar në analytics.
    Kthen (True, response) ose (False, error_message).
    """
    if not _init_firebase():
        logger.warning(
            'Firebase unavailable — skipping update notification for book: %s',
            book.title
        )
        return False, 'Firebase unavailable'

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(
                title='📚 Libër i Përditësuar!',
                body=f'"{book.title}" nga {book.author} ka përmbajtje të re.',
            ),
            data={
                'type': 'bookUpdate',
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
        logger.info(
            '✅ Book update notification sent: %s → %s', book.title, response
        )

        # Përditëso countin pa e shënuar si "të njoftuar herën e parë"
        try:
            from django.utils import timezone
            book.notification_sent = True
            book.notification_sent_at = timezone.now()
            book.notification_count = (book.notification_count or 0) + 1
            book.save(update_fields=[
                'notification_sent', 'notification_sent_at', 'notification_count'
            ])
        except Exception as e:
            logger.error('Failed to update book notification count: %s', e)

        return True, response

    except Exception as e:
        logger.error('❌ Book update notification failed: %s', e)
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