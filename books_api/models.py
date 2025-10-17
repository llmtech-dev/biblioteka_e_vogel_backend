from django.db import models
import uuid



class BookCategory(models.TextChoices):
    EDUKATE_ISLAME = 'edukateIslame', 'Edukate Islame'
    JETA_E_SAHABEVE = 'jetaESahabeve', 'Jeta e Sahabeve'
    HISTORITE_E_PROFETEVE = 'historiteEProfeteve', 'Historitë e Profeteve'
    HISTORI_NGA_KURANI = 'historiNgaKurani', 'Histori nga Kurani'
    NAMAZI_DHE_ADHURIMET = 'namaziDheAdhurimet', 'Namazi dhe Adhurimet'
    DUAT_PER_FEMIJE = 'duatPerFemije', 'Duatë per Femije'
    ETIKE_DHE_VLERA = 'etikeDheVlera', 'Etike dhe Vlera'
    NGJARJE_INSPIRUESE = 'ngjarjeInspiruese', 'Ngjarje Inspiruese'
    ANECDOTA_HUMORISTIKE = 'anecdotaHumoristikeMeMesim', 'Anekdota Humoristike'
    FESTE_ISLAME = 'festeIslame', 'Feste Islame'
    SHKENCA_DHE_ISLAMI = 'shkencaDheIslami', 'Shkenca dhe Islami'
    ART_DHE_KREATIVITET = 'artDheKreativitetIslamik', 'Art dhe Kreativitet'
    RREGULLA_TE_PERDITSHME = 'rregullaTePerditshmeIslame', 'Rregulla te Perditshme'
    TJETER = 'tjeter', 'Tjeter'


class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    translator = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=50, choices=BookCategory.choices)

    # Cover image - zgjedh njërën
    cover_image = models.URLField(max_length=500, blank=True, null=True,
                                  help_text='URL e jashtme (opsionale nëse ngarkon file)')
    pdf_path = models.URLField(max_length=500, blank=True, null=True)

    # File uploads
    cover_file = models.ImageField(upload_to='covers/', blank=True, null=True,
                                   help_text='Ngarko imazh nga kompjuteri')
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)

    send_push_now = models.BooleanField(
        default=False,
        verbose_name='Dërgo njoftim',
        help_text='✓ Shëno për të dërguar push notification kur ruhet libri'
    )

    cover_public_id = models.CharField(max_length=255, blank=True, null=True)
    pdf_public_id = models.CharField(max_length=255, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)

    # Tracking i njoftimeve
    notification_sent = models.BooleanField(default=False, verbose_name='Njoftimi u dërgua')
    notification_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Dërguar më')
    notification_count = models.IntegerField(default=0, verbose_name='Nr. njoftimesh')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_cover_url(self):
        """Kthen URL-në e cover - prioritet për Cloudinary URL"""
        # Nëse ka Cloudinary URL (nga upload ose manual)
        if self.cover_image:
            return self.cover_image
        # Nëse ka file lokal (për backwards compatibility)
        if self.cover_file:
            return self.cover_file.url
        return ''

    def save(self, *args, **kwargs):
        """Save me logjikë për notification"""
        is_new = self.pk is None
        should_send_push = self.send_push_now

        # Get old instance për krahasim nëse është update
        old_instance = None
        if not is_new and should_send_push:
            try:
                old_instance = Book.objects.get(pk=self.pk)
            except Book.DoesNotExist:
                pass

        # Reset send_push_now
        if should_send_push:
            self.send_push_now = False

        # Save normal
        super().save(*args, **kwargs)

        # Send notification nëse u kërkua
        if should_send_push and self.is_active and self.pk:
            from django.db import transaction

            def send_notification():
                from notifications_api.services import send_book_notification, send_book_update_notification

                # Determine notification type
                if is_new or not self.notification_sent:
                    # New book or first time notification
                    send_book_notification(self)
                else:
                    # Update notification
                    send_book_update_notification(self, old_instance)

            transaction.on_commit(send_notification)




class BookPage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()

    class Meta:
        ordering = ['page_number']
        unique_together = ['book', 'page_number']

    def __str__(self):
        return f"{self.book.title} - Faqja {self.page_number}"


class PageElement(models.Model):
    ELEMENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
    ]

    page = models.ForeignKey(BookPage, on_delete=models.CASCADE, related_name='elements')
    type = models.CharField(max_length=10, choices=ELEMENT_TYPES)
    content = models.TextField()
    position = models.IntegerField()
    image_file = models.ImageField(upload_to='page_images/', blank=True, null=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.page.book.title} - Faqja {self.page.page_number} - {self.type}"