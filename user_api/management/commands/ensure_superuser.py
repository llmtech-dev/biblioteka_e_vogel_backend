# user_api/management/commands/ensure_superuser.py
#
# Krijon (ose perditeson fjalekalimin e) nje superuser nga env vars —
# DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD / DJANGO_SUPERUSER_NAME.
# Idempotent — i sigurte te thirret ne çdo nisje te kontejnerit (shih
# docker-entrypoint.sh), ndryshe nga `createsuperuser --noinput` i
# Django-s qe deshton nese useri ekziston tashme.
#
# Perdorim (Render): vendos DJANGO_SUPERUSER_EMAIL/PASSWORD/NAME te
# Environment Variables. Nese s'jane vendosur, komanda thjesht anashkalohet
# (s'plas build-in nese dikush zgjedh te mos kete admin bootstrap).

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Krijon ose perditeson nje superuser nga DJANGO_SUPERUSER_EMAIL/'
        'PASSWORD/NAME (env vars). Anashkalohet nese s\'jane vendosur.'
    )

    def handle(self, *args, **options):
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '').strip()
        name = os.getenv('DJANGO_SUPERUSER_NAME', 'Admin').strip()

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_EMAIL/PASSWORD s\'jane vendosur — '
                'anashkalohet krijimi i superuser-it.'
            ))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'name': name},
        )
        user.name = name
        user.is_staff = True
        user.is_superuser = True
        user.role = User.Role.ADMIN
        user.set_password(password)
        user.save()

        action = 'krijuar' if created else 'perditesuar (fjalekalimi u rifreskua)'
        self.stdout.write(self.style.SUCCESS(f'Superuser "{email}" u {action}.'))
