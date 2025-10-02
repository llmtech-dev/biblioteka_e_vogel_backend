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
    id = models.CharField(max_length=100, primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    translator = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=50, choices=BookCategory.choices)
    cover_image = models.URLField(max_length=500)
    pdf_path = models.URLField(max_length=500, blank=True, null=True)

    # File uploads për imazhe dhe PDF
    cover_file = models.ImageField(upload_to='covers/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BookPage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()

    class Meta:
        ordering = ['page_number']
        unique_together = ['book', 'page_number']


class PageElement(models.Model):
    ELEMENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
    ]

    page = models.ForeignKey(BookPage, on_delete=models.CASCADE, related_name='elements')
    type = models.CharField(max_length=10, choices=ELEMENT_TYPES)
    content = models.TextField()
    position = models.IntegerField()

    # Për ruajtjen e imazheve
    image_file = models.ImageField(upload_to='page_images/', blank=True, null=True)

    class Meta:
        ordering = ['position']