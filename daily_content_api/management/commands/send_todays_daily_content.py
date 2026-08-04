# daily_content_api/management/commands/send_todays_daily_content.py
#
# Thirret nga nje scheduler i jashtem (Render Cron Job, PythonAnywhere
# "Scheduled Tasks", ose GitHub Actions cron) nje here/dite ne mengjes —
# p.sh.:  python manage.py send_todays_daily_content
#
# S'kerkon Redis/Celery (shih docs/04-infrastruktura-hosting.md) —
# kjo eshte thjesht nje komande Django qe gjen permbajtjen e sotme dhe,
# nese s'eshte njoftuar akoma, dergon push notification.

from django.core.management.base import BaseCommand
from django.utils import timezone

from daily_content_api.models import DailyContent


class Command(BaseCommand):
    help = 'Dergon push notification per permbajtjen ditore te sotme, nese s\'eshte dergu akoma.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        content = DailyContent.objects.filter(
            is_active=True, publish_date=today
        ).first()

        if not content:
            self.stdout.write(
                self.style.WARNING(f'Nuk ka përmbajtje ditore për {today}.')
            )
            return

        if content.notification_sent:
            self.stdout.write(
                self.style.WARNING(f'Përmbajtja e {today} është njoftuar tashmë.')
            )
            return

        from notifications_api.services import send_daily_content_notification
        success, response = send_daily_content_notification(content)

        if success:
            self.stdout.write(self.style.SUCCESS(f'Njoftimi u dërgua: {content}'))
        else:
            self.stdout.write(self.style.ERROR(f'Njoftimi dështoi: {response}'))
