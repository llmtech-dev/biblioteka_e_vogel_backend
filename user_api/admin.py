# user_api/admin.py
# ZËVENDËSO skedarin bosh ekzistues me këtë

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Panel i plotë i menaxhimit të përdoruesve.
    Moderatoret krijohen nga këtu — shih 'Roli' fushën.
    """
    model = CustomUser

    list_display  = ['email', 'name', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter   = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering      = ['-date_joined']

    # Faqja e ndryshimit të user-it ekzistues
    fieldsets = (
        ('Kredencialet', {
            'fields': ('email', 'password')
        }),
        ('Informacioni personal', {
            'fields': ('name',)
        }),
        ('Roli dhe aksesi', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser'),
            'description': (
                'MODERATORE: Vendos role=moderator dhe is_staff=True. '
                'ADMIN: role=admin, is_staff=True, is_superuser=True.'
            ),
        }),
        ('Grupet dhe lejet', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Datat', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    # Faqja e krijimit të user-it të ri
    add_fieldsets = (
        ('Krijo përdorues të ri', {
            'classes': ('wide',),
            'fields': (
                'email', 'name', 'role',
                'password1', 'password2',
                'is_active', 'is_staff',
            ),
        }),
    )