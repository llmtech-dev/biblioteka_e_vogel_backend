from django.contrib import admin
from .models import DailyContent


@admin.register(DailyContent)
class DailyContentAdmin(admin.ModelAdmin):
    list_display = ['publish_date', 'type', 'title', 'is_active', 'notification_sent']
    list_filter = ['type', 'is_active', 'notification_sent']
    search_fields = ['title', 'text', 'source']
    date_hierarchy = 'publish_date'
    readonly_fields = ['id', 'created_at', 'updated_at', 'notification_sent',
                        'notification_sent_at', 'notification_count']

    fieldsets = (
        ('Përmbajtja', {
            'fields': ('type', 'title', 'text', 'source', 'explanation'),
        }),
        ('Audio (opsionale — vetëm për sure)', {
            'fields': ('audio_file', 'audio_url'),
            'classes': ('collapse',),
        }),
        ('Publikimi', {
            'fields': ('publish_date', 'is_active', 'send_push_now'),
        }),
        ('Info', {
            'fields': ('id', 'notification_sent', 'notification_sent_at',
                       'notification_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
