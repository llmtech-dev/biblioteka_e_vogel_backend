# quiz_api/management/commands/import_quizzes.py
from django.core.management.base import BaseCommand
from django.db import transaction
import json
from books_api.models import Book
from quiz_api.models import Quiz, Question, AnswerOption


class Command(BaseCommand):
    help = 'Import quizzes from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON file with quizzes'
        )
        parser.add_argument(
            '--send-notification',
            action='store_true',
            help='Send push notification after import'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_file = options['json_file']
        send_notification = options['send_notification']

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                quizzes_data = json.load(f)

            created_count = 0
            updated_count = 0

            for quiz_data in quizzes_data:
                # Get book
                book_id = quiz_data.get('bookId', quiz_data.get('book_id'))
                try:
                    book = Book.objects.get(id=book_id)
                except Book.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Book {book_id} not found, skipping quiz"
                        )
                    )
                    continue

                # Create or update quiz
                quiz, created = Quiz.objects.update_or_create(
                    id=quiz_data.get('id'),
                    defaults={
                        'book': book,
                        'title': quiz_data['title'],
                        'send_push_now': send_notification
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Delete existing questions
                quiz.questions.all().delete()

                # Add questions
                for idx, q_data in enumerate(quiz_data.get('questions', [])):
                    question = Question.objects.create(
                        id=q_data.get('id'),
                        quiz=quiz,
                        text=q_data['text'],
                        correct_option_index=q_data.get(
                            'correctOptionIndex',
                            q_data.get('correct_option_index', 0)
                        ),
                        order=idx
                    )

                    # Add options
                    for opt_idx, opt_data in enumerate(q_data.get('options', [])):
                        if isinstance(opt_data, dict):
                            text = opt_data.get('text', '')
                        else:
                            text = str(opt_data)

                        AnswerOption.objects.create(
                            question=question,
                            text=text,
                            order=opt_idx
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{'Created' if created else 'Updated'} quiz: {quiz.title}"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Import completed!"
                    f"\n   Created: {created_count} quizzes"
                    f"\n   Updated: {updated_count} quizzes"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error importing quizzes: {str(e)}")
            )
            raise