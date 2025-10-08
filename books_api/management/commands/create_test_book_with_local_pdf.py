# books_api/management/commands/create_test_book_with_local_pdf.py
import os
import uuid
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files import File
from django.conf import settings
from books_api.models import Book, BookPage, PageElement
from quizes_api.models import Quiz, Question, AnswerOption
from notifications_api.services import send_book_notification, send_quiz_notification


class Command(BaseCommand):
    help = 'Create a test book with local PDF and images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf',
            type=str,
            default='zubejri.pdf',
            help='PDF filename in project root'
        )
        parser.add_argument(
            '--send-notification',
            action='store_true',
            help='Send notification after creating'
        )

    def handle(self, *args, **options):
        pdf_filename = options['pdf']
        send_notification = options['send_notification']

        # 1. Krijo test book
        book = Book.objects.create(
            title="Test: Historia e Zubejrit",
            author="Test Author",
            translator="Test Translator",
            category="jetaESahabeve",
            is_active=True,
            version=1
        )

        self.stdout.write(f'✅ Created book: {book.title} (ID: {book.id})')

        # 2. Shto PDF nga file lokale
        pdf_path = os.path.join(settings.BASE_DIR, pdf_filename)

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                book.pdf_file.save(pdf_filename, File(pdf_file))
                book.pdf_path = book.pdf_file.url
                book.save()
                self.stdout.write(f'✅ Added PDF: {pdf_filename}')
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ PDF not found at {pdf_path}')
            )

        # 3. Shto cover image (përdor një test image)
        try:
            # Krijo një cover image të thjeshtë me Pillow
            from PIL import Image, ImageDraw, ImageFont
            import io

            # Krijo image
            img = Image.new('RGB', (300, 400), color='#4CAF50')
            draw = ImageDraw.Draw(img)

            # Shto tekst
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
            except:
                font = ImageFont.load_default()

            draw.text((20, 150), "HISTORIA E\nZUBEJRIT", fill='white', font=font)

            # Ruaj si bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            # Ruaj në model
            book.cover_file.save(f'cover_{book.id}.jpg', ContentFile(img_bytes.read()))
            book.cover_image = book.cover_file.url
            book.save()
            self.stdout.write('✅ Created cover image')

        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️ Pillow not installed, using placeholder URL')
            )
            book.cover_image = 'https://via.placeholder.com/300x400/4CAF50/FFFFFF?text=Zubejri'
            book.save()

        # 4. Shto pages me content
        # Page 1
        page1 = BookPage.objects.create(book=book, page_number=1)

        PageElement.objects.create(
            page=page1,
            type='text',
            content='Zubejr ibn Avami (r.a) ishte një nga dhjetë sahabët të cilëve Profeti (a.s) u dha përgëzimin e xhenetit. Ai ishte hallai i Profetit dhe nga miqtë më të afërt të tij.',
            position=0
        )

        # Shto një image element
        PageElement.objects.create(
            page=page1,
            type='image',
            content='https://via.placeholder.com/400x300/2196F3/FFFFFF?text=Zubejr+ibn+Avam',
            position=1
        )

        # Page 2
        page2 = BookPage.objects.create(book=book, page_number=2)

        PageElement.objects.create(
            page=page2,
            type='text',
            content='Zubejri ishte i njohur për trimërinë dhe devotshmërinë e tij. Ai mori pjesë në të gjitha betejat e rëndësishme të Islamit dhe ishte një nga shtylla e Islamit.',
            position=0
        )

        PageElement.objects.create(
            page=page2,
            type='text',
            content='Profeti (a.s) ka thënë për të: "Çdo profet ka pasur një ndihmës, dhe ndihmësi im është Zubejri."',
            position=1
        )

        # Page 3
        page3 = BookPage.objects.create(book=book, page_number=3)

        PageElement.objects.create(
            page=page3,
            type='text',
            content='Një nga cilësitë më të spikatura të Zubejrit ishte bujaria e tij. Ai ishte një tregtar i suksesshëm por asnjëherë nuk harroi të ndihmonte të varfrit dhe nevojtarët.',
            position=0
        )

        self.stdout.write(f'✅ Added {book.pages.count()} pages with content')

        # 5. Krijo quiz për librin
        quiz = Quiz.objects.create(
            book=book,
            title=f"Quiz - {book.title}"
        )

        # Question 1
        q1 = Question.objects.create(
            quiz=quiz,
            text="Çfarë lidhjeje kishte Zubejri me Profetin Muhamed (a.s)?",
            correct_option_index=2,
            order=0
        )

        AnswerOption.objects.create(question=q1, text="Kushëri", order=0)
        AnswerOption.objects.create(question=q1, text="Dajë", order=1)
        AnswerOption.objects.create(question=q1, text="Halla", order=2)
        AnswerOption.objects.create(question=q1, text="Nuk kishin lidhje", order=3)

        # Question 2
        q2 = Question.objects.create(
            quiz=quiz,
            text="Çfarë ka thënë Profeti për Zubejrin?",
            correct_option_index=1,
            order=1
        )

        AnswerOption.objects.create(question=q2, text="Ai është shpata ime", order=0)
        AnswerOption.objects.create(question=q2, text="Ai është ndihmësi im", order=1)
        AnswerOption.objects.create(question=q2, text="Ai është mbrojtësi im", order=2)
        AnswerOption.objects.create(question=q2, text="Ai është vëllai im", order=3)

        # Question 3
        q3 = Question.objects.create(
            quiz=quiz,
            text="Sa sahabë morën përgëzimin e xhenetit nga Profeti?",
            correct_option_index=0,
            order=2
        )

        AnswerOption.objects.create(question=q3, text="Dhjetë", order=0)
        AnswerOption.objects.create(question=q3, text="Pesë", order=1)
        AnswerOption.objects.create(question=q3, text="Njëzet", order=2)
        AnswerOption.objects.create(question=q3, text="Tetë", order=3)

        self.stdout.write(f'✅ Created quiz with {quiz.questions.count()} questions')

        # 6. Dërgo notification nëse është kërkuar
        if send_notification:
            # Për book
            success, response = send_book_notification(book)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'📚 Book notification sent: {response}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Book notification failed: {response}')
                )

            # Prit pak
            import time
            time.sleep(2)

            # Për quiz
            success, response = send_quiz_notification(quiz)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'🎯 Quiz notification sent: {response}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Quiz notification failed: {response}')
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Test book created successfully!\n'
                f'   Book ID: {book.id}\n'
                f'   Title: {book.title}\n'
                f'   Pages: {book.pages.count()}\n'
                f'   Quiz questions: {quiz.questions.count()}\n'
                f'   PDF: {book.pdf_path}\n'
                f'   Cover: {book.cover_image}'
            )
        )