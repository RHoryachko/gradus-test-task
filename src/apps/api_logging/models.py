from django.db import models
from django.contrib.auth.models import User


class APILog(models.Model):
    """Model for logging API requests"""
    
    method = models.CharField(max_length=10, verbose_name='HTTP Method')
    path = models.CharField(max_length=500, verbose_name='Path')
    query_params = models.JSONField(default=dict, blank=True, verbose_name='Query Parameters')
    request_body = models.TextField(blank=True, null=True, verbose_name='Request Body')
    response_status = models.IntegerField(verbose_name='Response Status Code')
    response_body = models.TextField(blank=True, null=True, verbose_name='Response Body')
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='User'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    user_agent = models.CharField(max_length=500, blank=True, null=True, verbose_name='User Agent')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    duration_ms = models.FloatField(null=True, blank=True, verbose_name='Duration (ms)')
    
    error_message = models.TextField(blank=True, null=True, verbose_name='Error Message')
    error_traceback = models.TextField(blank=True, null=True, verbose_name='Error Traceback')
    
    class Meta:
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['response_status']),
            models.Index(fields=['method', 'path']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.response_status} ({self.created_at})"
    
    def is_error(self):
        """Check if response is an error (4xx or 5xx)"""
        return 400 <= self.response_status < 600
    is_error.boolean = True
    
    def is_success(self):
        """Check if response is successful (2xx)"""
        return 200 <= self.response_status < 300
    is_success.boolean = True
