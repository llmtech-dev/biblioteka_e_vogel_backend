# daily_content_api/models.py
#
# "Permbajtja e dites" — ajet, hadith, keshille, ose sure e shkurter me
# audio, e publikuar nga moderatoret dhe e shperndare nje here/dite.
# Faza 5 (docs/05-ide-permiresimi-features.md § Shtresa 1).

import uuid
from django.db import models


class DailyContent(models.Model):
    class ContentType(models.TextChoices):
        AYAH = 'ayah', 'Ajet Kuranor'
        HADITH = 'hadith', 'Hadith'
        ADVICE = 'advice', 'Këshillë'
        SURAH_AUDIO = 'surah_audio', 'Sure e shkurtër (audio)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=ContentType.choices)

    title = models.CharField(
        max_length=255, blank=True,
        help_text='P.sh. "Ajeti i ditës" — opsionale, gjenerohet automatikisht nëse bosh.'
    )
    text = models.TextField(help_text='Teksti kryesor — ajeti/hadithi/këshilla në shqip.')
    source = models.CharField(
        max_length=255, blank=True,
        help_text='P.sh. "Bukhari 1:1" ose "Sure El-Bekare, ajeti 255".'
    )
    explanation = models.TextField(
        blank=True, help_text='Shpjegim i shkurtër (tefsir/kontekst) — opsional.'
    )

    # Audio (per sure te shkurtra) — file lokal/Cloudinary OSE URL e jashtme.
    audio_file = models.FileField(upload_to='daily_audio/', blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True)
    audio_public_id = models.CharField(max_length=255, blank=True)

    publish_date = models.DateField(
        unique=True, help_text='Dita kur shfaqet — një përmbajtje për ditë.'
    )
    is_active = models.BooleanField(default=True)

    send_push_now = models.BooleanField(
        default=False,
        verbose_name='Dërgo njoftim',
        help_text='✓ Shëno për të dërguar push notification kur ruhet.'
    )
    notification_sent = models.BooleanField(default=False, verbose_name='Njoftimi u dërgua')
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    notification_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publish_date']
        verbose_name_plural = 'Daily Content'

    def __str__(self):
        return f'{self.get_type_display()} — {self.publish_date}'

    def get_audio_url(self):
        if self.audio_url:
            return self.audio_url
        if self.audio_file:
            return self.audio_file.url
        return ''

    def save(self, *args, **kwargs):
        """Save me logjike per notification — njesoj si Book/Quiz."""
        should_send_push = self.send_push_now
        if should_send_push:
            self.send_push_now = False

        super().save(*args, **kwargs)

        if should_send_push and self.is_active and self.pk:
            from django.db import transaction

            def send_notification():
                from notifications_api.services import send_daily_content_notification
                send_daily_content_notification(self)

            transaction.on_commit(send_notification)
