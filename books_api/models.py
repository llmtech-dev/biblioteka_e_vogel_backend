from django.db import models
from django.utils import timezone
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
        """Kthen URL-në e cover - prioritet për file të ngarkuar"""
        if self.cover_file:
            return self.cover_file.url
        return self.cover_image or ''

    def save(self, *args, **kwargs):
        """Auto-populate cover_image nga cover_file nëse nuk është vendosur"""
        if self.cover_file and not self.cover_image:
            # Save për të marrë URL-në e file
            super().save(*args, **kwargs)
            # Pas save-it, cover_file.url është i disponueshëm
            if not self.cover_image:
                self.cover_image = self.cover_file.url
                super().save(update_fields=['cover_image'])
        else:
            super().save(*args, **kwargs)


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