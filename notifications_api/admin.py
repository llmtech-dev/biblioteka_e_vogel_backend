from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']

    actions = ['activate_notifications', 'deactivate_notifications']

    def activate_notifications(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} njoftime u aktivizuan")

    activate_notifications.short_description = "Aktivizo njoftimet e zgjedhura"

    def deactivate_notifications(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} njoftime u çaktivizuan")

    deactivate_notifications.short_description = "Çaktivizo njoftimet e zgjedhura"