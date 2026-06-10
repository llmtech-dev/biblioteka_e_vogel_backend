# user_api/models.py
# ZËVENDËSO me këtë version — shton fushën 'role' dhe create_moderator()

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, name, password, **extra_fields)

    def create_moderator(self, email, name, password):
        """Krijo moderatore nga shell: CustomUser.objects.create_moderator(...)"""
        return self.create_user(
            email=email,
            name=name,
            password=password,
            role='moderator',
            is_staff=True,
            is_superuser=False,
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN     = 'admin',     'Administrator'
        MODERATOR = 'moderator', 'Moderatore'
        USER      = 'user',      'Përdorues'

    email    = models.EmailField(unique=True)
    name     = models.CharField(max_length=100)
    role     = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Roli',
    )
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    @property
    def is_moderator(self):
        return self.role in [self.Role.MODERATOR, self.Role.ADMIN]

    def __str__(self):
        return f'{self.email} ({self.role})'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)