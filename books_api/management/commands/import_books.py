import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from books_api.models import Book, BookPage, PageElement


class Command(BaseCommand):
    help = 'Import books from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='books.json',
            help='Path to JSON file (default: books.json in project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing books before import'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        # Nëse nuk është path i plotë, kontrollo në root të projektit
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        # Lexo JSON file
        self.stdout.write(f'Reading file: {file_path}')
        with open(file_path, 'r', encoding='utf-8') as file:
            books_data = json.load(file)

        # Clear existing nëse është specifikuar
        if options['clear']:
            self.stdout.write('Clearing existing books...')
            Book.objects.all().delete()
            self.stdout.write(self.style.WARNING('All books deleted!'))

        # Import books
        created_count = 0
        updated_count = 0

        for book_data in books_data:
            self.stdout.write(f"Processing book: {book_data['title']}")

            # Konverto paths nga Flutter në Django paths
            cover_image = book_data['coverImage'].replace('assets/', '/static/')
            pdf_path = book_data.get('pdfPath', '').replace('assets/', '/static/')

            # Krijo ose përditëso librin
            book, created = Book.objects.update_or_create(
                id=book_data['id'],
                defaults={
                    'title': book_data['title'],
                    'author': book_data['author'],
                    'translator': book_data.get('translator', ''),
                    'category': book_data['category'],
                    'cover_image': cover_image,
                    'pdf_path': pdf_path,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created book: {book.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated book: {book.title}')
                )

            # Fshi faqet ekzistuese dhe krijo të rejat
            book.pages.all().delete()

            # Import pages
            for page_index, page_data in enumerate(book_data.get('pages', [])):
                page = BookPage.objects.create(
                    book=book,
                    page_number=page_index + 1
                )

                # Import elements
                for element_data in page_data.get('elements', []):
                    # Konverto image paths
                    content = element_data['content']
                    if element_data['type'] == 'image':
                        content = content.replace('assets/', '/static/')

                    PageElement.objects.create(
                        page=page,
                        type=element_data['type'],
                        content=content,
                        position=element_data['position']
                    )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed! Created: {created_count}, Updated: {updated_count}'
            )
        )