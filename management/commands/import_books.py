from books_api.models import Book


def import_books(self, books_data):
    for book_data in books_data:
        # Konverto paths nga Flutter në Django paths
        cover_image = book_data['coverImage'].replace('assets/', '/static/')
        pdf_path = book_data.get('pdfPath', '').replace('assets/', '/static/')

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