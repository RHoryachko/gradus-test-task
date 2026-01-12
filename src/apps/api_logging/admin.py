from django.contrib import admin
from apps.api_logging.models import APILog


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    """Admin interface for API logs"""
    
    list_display = [
        'id', 'method', 'path_short', 'response_status', 
        'user', 'ip_address', 'duration_ms', 'created_at'
    ]
    list_filter = [
        'method', 'response_status', 'created_at', 'user'
    ]
    search_fields = ['path', 'ip_address', 'user__username', 'error_message']
    readonly_fields = [
        'method', 'path', 'query_params', 'request_body', 
        'response_status', 'response_body', 'user', 'ip_address', 
        'user_agent', 'created_at', 'duration_ms', 'error_message', 
        'error_traceback'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('method', 'path', 'query_params', 'request_body', 'user', 'ip_address', 'user_agent')
        }),
        ('Response Information', {
            'fields': ('response_status', 'response_body', 'duration_ms')
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def path_short(self, obj):
        """Display shortened path"""
        if len(obj.path) > 50:
            return obj.path[:47] + '...'
        return obj.path
    path_short.short_description = 'Path'
    
    def has_add_permission(self, request):
        """Disable adding logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deleting logs"""
        return True
