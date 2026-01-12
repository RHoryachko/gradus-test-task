import json
import time
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.db import transaction

from apps.api_logging.models import APILog


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging all API requests and responses
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._api_log_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log API request and response"""
        # Only log API requests (starting with /api/)
        if not request.path.startswith('/api/'):
            return response
        
        try:
            # Calculate duration
            duration_ms = None
            if hasattr(request, '_api_log_start_time'):
                duration_ms = (time.time() - request._api_log_start_time) * 1000
            
            # Get request body
            request_body = None
            if request.body:
                try:
                    # Try to parse as JSON
                    body_str = request.body.decode('utf-8')
                    if body_str:
                        json.loads(body_str)  # Validate JSON
                        request_body = body_str
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # If not JSON, store as string (truncated)
                    request_body = request.body.decode('utf-8', errors='ignore')[:1000]
            
            # Get response body
            response_body = None
            if hasattr(response, 'content'):
                try:
                    content_str = response.content.decode('utf-8')
                    if content_str:
                        # Try to parse as JSON for better formatting
                        try:
                            json.loads(content_str)
                            response_body = content_str[:5000]  # Limit size
                        except json.JSONDecodeError:
                            response_body = content_str[:1000]  # Limit size
                except UnicodeDecodeError:
                    response_body = None
            
            # Get user
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # Get IP address
            ip_address = self.get_client_ip(request)
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # Get query parameters
            query_params = dict(request.GET)
            
            # Create log entry (use atomic transaction to avoid blocking)
            with transaction.atomic():
                APILog.objects.create(
                    method=request.method,
                    path=request.path,
                    query_params=query_params,
                    request_body=request_body,
                    response_status=response.status_code,
                    response_body=response_body,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    duration_ms=duration_ms,
                )
        
        except Exception as e:
            # Don't break the request if logging fails
            # In production, use proper logging
            pass
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None
        
        try:
            # Calculate duration
            duration_ms = None
            if hasattr(request, '_api_log_start_time'):
                duration_ms = (time.time() - request._api_log_start_time) * 1000
            
            # Get request body
            request_body = None
            if request.body:
                try:
                    body_str = request.body.decode('utf-8')
                    if body_str:
                        json.loads(body_str)
                        request_body = body_str
                except (UnicodeDecodeError, json.JSONDecodeError):
                    request_body = request.body.decode('utf-8', errors='ignore')[:1000]
            
            # Get user
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # Get IP address
            ip_address = self.get_client_ip(request)
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # Get query parameters
            query_params = dict(request.GET)
            
            # Get error details
            error_message = str(exception)
            error_traceback = traceback.format_exc()
            
            # Create log entry
            with transaction.atomic():
                APILog.objects.create(
                    method=request.method,
                    path=request.path,
                    query_params=query_params,
                    request_body=request_body,
                    response_status=500,  # Internal server error
                    response_body=None,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    error_traceback=error_traceback,
                )
        
        except Exception:
            # Don't break the request if logging fails
            pass
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
