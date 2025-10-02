import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Import all data (books and quizzes) in correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--books-file',
            type=str,
            default='books.json',
            help='Path to books JSON file'
        )
        parser.add_argument(
            '--quizzes-file',
            type=str,
            default='quizzes.json',
            help='Path to quizzes JSON file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting full import...\n'))

        # Import books first (quizzes depend on books)
        self.stdout.write(self.style.NOTICE('Step 1: Importing books...'))
        call_command(
            'import_books',
            file=options['books_file'],
            clear=options['clear']
        )

        # Then import quizzes
        self.stdout.write(self.style.NOTICE('\nStep 2: Importing quizzes...'))
        call_command(
            'import_quizzes',
            file=options['quizzes_file'],
            clear=options['clear']
        )

        self.stdout.write(
            self.style.SUCCESS('\n✓ All data imported successfully!')
        )



        #perdorimi duke thirrur
        # python manage.py import_books
        """
        python manage.py import_books
# Ose me path specifik
python manage.py import_books --file=/path/to/books.json
# Ose duke fshirë të dhënat e vjetra
python manage.py import_books --clear


python manage.py import_all_data
# Ose me paths specifike
python manage.py import_all_data --books-file=books.json --quizzes-file=quizzes.json --clear
"""