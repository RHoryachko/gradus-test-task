from django.contrib import admin
from apps.notifications.models.gradus_models import (
    Variable,
    Channel,
    NotificationType,
    NotificationTemplate
)


@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'allowed_tags', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'is_custom', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_custom', 'is_active', 'created_at']
    search_fields = ['title']
    filter_horizontal = ['variables', 'channels']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'is_custom', 'is_active')
        }),
        ('Relations', {
            'fields': ('variables', 'channels')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'notification_type', 'channel', 'name', 'title', 'is_active', 'created_at']
    list_filter = ['notification_type', 'channel', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'notification_type__title', 'channel__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification_type', 'channel', 'name', 'title', 'is_active')
        }),
        ('Template Content', {
            'fields': ('html',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
