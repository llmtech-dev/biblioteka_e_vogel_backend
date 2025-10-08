# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from .models import Book
# from firebase_admin import messaging
# import firebase_admin
# from firebase_admin import credentials
#
# # Initialize Firebase Admin SDK (bëje në settings.py ose apps.py)
# if not firebase_admin._apps:
#     cred = credentials.Certificate('firebase-credentials.json')
#     firebase_admin.initialize_app(cred)
#
#
# @receiver(post_save, sender=Book)
# def send_book_notification(sender, instance, created, **kwargs):
#     """Dërgon push notification kur shtohet libër i ri"""
#     if created or not created and not instance.notification_sent:
#         try:
#             # Krijo mesazhin
#             message = messaging.Message(
#                 notification=messaging.Notification(
#                     title='📚 Libër i ri!',
#                     body=f'{instance.title} nga {instance.author}',
#                     image=instance.get_cover_url() if instance.get_cover_url() else None
#                 ),
#                 data={
#                     'type': 'new_book',
#                     'book_id': str(instance.id),
#                     'book_title': instance.title,
#                     'book_author': instance.author,
#                     'book_category': instance.category,
#                     'cover_url': instance.get_cover_url() or '',
#                     'click_action': 'FLUTTER_NOTIFICATION_CLICK',
#                 },
#                 topic='new_books',  # Topic subscription
#             )
#
#             # Dërgo mesazhin
#             response = messaging.send(message)
#
#             # Update book notification status
#             instance.notification_sent = True
#             instance.notification_sent_at = timezone.now()
#             instance.notification_count = 1
#             instance.save(update_fields=['notification_sent', 'notification_sent_at', 'notification_count'])
#
#             print(f'Successfully sent message for book {instance.title}: {response}')
#
#         except Exception as e:
#             print(f'Error sending notification for book {instance.title}: {e}')