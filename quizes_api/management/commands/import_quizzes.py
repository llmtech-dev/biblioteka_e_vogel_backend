import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from quizes_api.models import Quiz, Question, AnswerOption
from books_api.models import Book


class Command(BaseCommand):
    help = 'Import quizzes from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='quizzes.json',
            help='Path to JSON file (default: quizzes.json in project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing quizzes before import'
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
            quizzes_data = json.load(file)

        # Clear existing nëse është specifikuar
        if options['clear']:
            self.stdout.write('Clearing existing quizzes...')
            Quiz.objects.all().delete()
            self.stdout.write(self.style.WARNING('All quizzes deleted!'))

        # Import quizzes
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for quiz_data in quizzes_data:
            self.stdout.write(f"Processing quiz: {quiz_data['title']}")

            # Kontrollo nëse libri ekziston
            try:
                book = Book.objects.get(id=quiz_data['bookId'])
            except Book.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Skipped quiz: Book with id {quiz_data["bookId"]} not found'
                    )
                )
                skipped_count += 1
                continue

            # Krijo ose përditëso quiz-in
            quiz, created = Quiz.objects.update_or_create(
                id=quiz_data['id'],
                defaults={
                    'book': book,
                    'title': quiz_data['title'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created quiz: {quiz.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated quiz: {quiz.title}')
                )

            # Menaxho questions - përdor update_or_create
            existing_question_ids = []

            for q_index, question_data in enumerate(quiz_data.get('questions', [])):
                question, q_created = Question.objects.update_or_create(
                    id=question_data['id'],
                    defaults={
                        'quiz': quiz,
                        'text': question_data['text'],
                        'correct_option_index': question_data['correctOptionIndex'],
                        'order': q_index
                    }
                )
                existing_question_ids.append(question.id)

                if q_created:
                    self.stdout.write(f'  + Added question: {question.text[:50]}...')

                # Menaxho answer options
                existing_option_ids = []

                for opt_index, option_data in enumerate(question_data.get('options', [])):
                    option, opt_created = AnswerOption.objects.update_or_create(
                        question=question,
                        order=opt_index,
                        defaults={
                            'text': option_data['text'],
                        }
                    )
                    existing_option_ids.append(option.id)

                # Fshi options që nuk janë më në JSON
                question.options.exclude(id__in=existing_option_ids).delete()

            # Fshi questions që nuk janë më në JSON
            quiz.questions.exclude(id__in=existing_question_ids).delete()

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed! Created: {created_count}, '
                f'Updated: {updated_count}, Skipped: {skipped_count}'
            )
        )


        """
        python manage.py import_quizzes
# Ose me opsione
python manage.py import_quizzes --file=quizzes.json --clear
        """