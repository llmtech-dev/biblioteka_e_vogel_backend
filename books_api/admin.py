from django.contrib import admin
from django.contrib import messages
from django import forms
from .models import Book, BookPage, PageElement
from notifications_api.services import send_book_notification
import uuid


class BookAdminForm(forms.ModelForm):
    # Përmbajtja e shpejtë për faqet
    quick_content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 15, 'cols': 80}),
        required=False,
        label="Përmbajtja e Librit",
        help_text="Shkruaj përmbajtjen këtu. Lër një rresht bosh për faqe të re."
    )

    # Dropdown për kopertina
    COVER_CHOICES = [
        ('', '-- Zgjidh Kopertinën --'),
        ('https://permamat.pythonanywhere.com/static/covers/histori.jpg', '📚 Histori (Blu)'),
        ('https://permamat.pythonanywhere.com/static/covers/namaz.jpg', '🕌 Namaz (Jeshile)'),
        ('https://permamat.pythonanywhere.com/static/covers/sahabe.jpg', '⭐ Sahabe (Portokalli)'),
        ('https://permamat.pythonanywhere.com/static/covers/dua.jpg', '🤲 Dua (Rozë)'),
        ('https://permamat.pythonanywhere.com/static/covers/edukim.jpg', '📖 Edukim (Vjollcë)'),
        ('auto', '🎨 Gjenero Automatikisht'),
    ]

    cover_choice = forms.ChoiceField(
        choices=COVER_CHOICES,
        label="Zgjidh Kopertinën",
        initial='auto'
    )

    # PDF filename
    pdf_filename = forms.CharField(
        max_length=100,
        required=False,
        label="Emri i PDF (opsionale)",
        help_text="Shembull: libri_i_namazit.pdf"
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'translator', 'category', 'is_active']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    list_display = ['title', 'author', 'category', 'page_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'author']

    fieldsets = (
        ('📝 Informacioni i Librit', {
            'fields': ('title', 'author', 'translator', 'category')
        }),
        ('🖼️ Kopertina', {
            'fields': ('cover_choice',)
        }),
        ('📄 PDF (Opsionale)', {
            'fields': ('pdf_filename',)
        }),
        ('✍️ Përmbajtja e Librit', {
            'fields': ('quick_content',)
        }),
        ('⚙️ Opsione', {
            'fields': ('is_active',)
        })
    )

    def page_count(self, obj):
        return obj.pages.count()

    page_count.short_description = "Faqe"

    def save_model(self, request, obj, form, change):
        # Auto ID
        if not obj.id:
            obj.id = f"lib_{uuid.uuid4().hex[:6]}"

        # Handle cover
        cover_choice = form.cleaned_data.get('cover_choice')
        if cover_choice == 'auto':
            colors = {
                'historiteEProfeteve': '2196F3',
                'namaziDheAdhurimet': '4CAF50',
                'jetaESahabeve': 'FF9800',
                'duatPerFemije': 'E91E63',
                'etikeDheVlera': '9C27B0',
            }
            color = colors.get(obj.category, '607D8B')
            obj.cover_image = f"https://dummyimage.com/200x300/{color}/FFFFFF.png&text={obj.title.replace(' ', '+')}"
        elif cover_choice:
            obj.cover_image = cover_choice

        # Handle PDF
        pdf_filename = form.cleaned_data.get('pdf_filename')
        if pdf_filename:
            if not pdf_filename.endswith('.pdf'):
                pdf_filename += '.pdf'
            obj.pdf_path = f"https://permamat.pythonanywhere.com/static/pdfs/{pdf_filename}"

        # Save book
        is_new = not change
        super().save_model(request, obj, form, change)

        # Create pages from content
        if is_new:
            content = form.cleaned_data.get('quick_content', '')
            if content:
                pages = [p.strip() for p in content.split('\n\n') if p.strip()]
                for i, page_text in enumerate(pages, 1):
                    page = BookPage.objects.create(book=obj, page_number=i)
                    PageElement.objects.create(
                        page=page,
                        type='text',
                        content=page_text,
                        position=0
                    )

            # Send notification
            if obj.is_active:
                try:
                    success, response = send_book_notification(obj)
                    if success:
                        messages.success(request, '✅ Libri u ruajt dhe njoftimi u dërgua!')
                except Exception as e:
                    messages.warning(request, f'⚠️ Libri u ruajt por njoftimi dështoi: {e}')


# from django.contrib import admin
# from django.contrib import messages
# from .models import Book, BookPage, PageElement
# from notifications_api.services import send_book_notification
#
#
# class PageElementInline(admin.TabularInline):
#     model = PageElement
#     extra = 1
#
#
# class BookPageInline(admin.TabularInline):
#     model = BookPage
#     extra = 1
#     show_change_link = True
#
#
# @admin.register(Book)
# class BookAdmin(admin.ModelAdmin):
#     list_display = ['id', 'title', 'author', 'category', 'is_active', 'created_at']
#     list_filter = ['category', 'is_active', 'created_at']
#     search_fields = ['title', 'author', 'translator']
#
#     inlines = [BookPageInline]
#
#     fieldsets = (
#         ('Informacioni Bazë', {
#             'fields': ('id', 'title', 'author', 'translator', 'category')
#         }),
#         ('Media', {
#             'fields': ('cover_image', 'cover_file', 'pdf_path', 'pdf_file')
#         }),
#         ('Statusi', {
#             'fields': ('is_active', 'version')
#         })
#     )
#
#     actions = ['send_notification_for_books']
#
#     def save_model(self, request, obj, form, change):
#         """Dërgo notification kur shtohet libër i ri"""
#         is_new = not change
#         super().save_model(request, obj, form, change)
#
#         # Dërgo notification vetëm për libra të rinj dhe aktiv
#         if is_new and obj.is_active:
#             try:
#                 success, response = send_book_notification(obj)
#                 if success:
#                     messages.success(
#                         request,
#                         f'✅ Njoftimi për librin u dërgua: {response}'
#                     )
#                 else:
#                     messages.warning(
#                         request,
#                         f'⚠️ Libri u ruajt por njoftimi nuk u dërgua: {response}'
#                     )
#             except Exception as e:
#                 messages.error(
#                     request,
#                     f'❌ Gabim në dërgimin e njoftimit: {str(e)}'
#                 )
#
#     def send_notification_for_books(self, request, queryset):
#         """Dërgo notification për librat e zgjedhur"""
#         sent = 0
#         for book in queryset.filter(is_active=True):
#             try:
#                 success, response = send_book_notification(book)
#                 if success:
#                     sent += 1
#             except:
#                 pass
#
#         messages.success(request, f'✅ U dërguan {sent} njoftime për libra')
#
#     send_notification_for_books.short_description = "Dërgo njoftim për librat e zgjedhur"