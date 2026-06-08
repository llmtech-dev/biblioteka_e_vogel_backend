# books_api/signals.py
# Dërgon automatikisht push notification kur krijohet libër i ri
# nëse send_push_now = True

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='books_api.Book')
def book_post_save(sender, instance, created, **kwargs):
    """
    Pas ruajtjes së librit:
    • Nëse created=True dhe send_push_now=True → dërgo njoftim
    • Nëse updated dhe send_push_now=True dhe nuk është njoftuar → dërgo
    """
    if not getattr(instance, 'send_push_now', False):
        return

    if instance.notification_sent:
        return  # Mos dërgo dy herë

    # Dërgo në background thread për të mos bllokuar request-in
    import threading
    def _send():
        from notifications_api.services import send_book_notification
        success, result = send_book_notification(instance)
        if success:
            logger.info('📬 Auto-notification sent for book: %s', instance.title)
        else:
            logger.error('📵 Auto-notification failed for book: %s — %s',
                         instance.title, result)

    t = threading.Thread(target=_send, daemon=True)
    t.start()


@receiver(post_save, sender='quizes_api.Quiz')
def quiz_post_save(sender, instance, created, **kwargs):
    """
    Pas ruajtjes së kuizit:
    • Nëse send_push_now=True dhe nuk është njoftuar → dërgo
    """
    if not getattr(instance, 'send_push_now', False):
        return

    if getattr(instance, 'notification_sent', False):
        return

    import threading
    def _send():
        from notifications_api.services import send_quiz_notification
        success, result = send_quiz_notification(instance)
        if success:
            logger.info('📬 Auto-notification sent for quiz: %s', instance.title)
        else:
            logger.error('📵 Auto-notification failed for quiz: %s — %s',
                         instance.title, result)

    t = threading.Thread(target=_send, daemon=True)
    t.start()
