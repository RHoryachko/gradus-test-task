from typing import Dict, Any, Optional
from django.template import Engine, Context
from django.core.mail import send_mail
from django.conf import settings

from apps.notifications.models.gradus_models import (
    NotificationType,
    NotificationTemplate,
    Channel
)


class NotificationSender:
    """
    Class for sending notifications via email
    
    Example:
        sender = NotificationSender()
        
        # Send notification
        sender.send(
            notification_type='new survey',
            context={'title': 'New Survey'},
            recipient='user@example.com'
        )
    """
    
    def send(
        self,
        notification_type: str,
        context: Dict[str, Any],
        recipient: str,
        template_name: Optional[str] = None
    ) -> bool:
        """
        Send notification via email
        
        Args:
            notification_type: Name of notification type (e.g. 'new survey', 'confirm email')
            context: Dictionary with variables for template (e.g. {'title': 'Hello'})
            recipient: Email address of recipient
            template_name: Name of template (only for custom types)
        
        Returns:
            True if sent successfully, False if error
        """
        try:
            notification_type_obj = NotificationType.objects.filter(
                title=notification_type,
                is_active=True
            ).first()
            
            if not notification_type_obj:
                raise ValueError(f"Тип нотифікації '{notification_type}' не знайдено")
            
            channel_obj = Channel.objects.filter(
                title='email',
                is_active=True
            ).first()
            
            if not channel_obj:
                raise ValueError("Channel 'email' not found")
            
            if channel_obj not in notification_type_obj.channels.all():
                raise ValueError(
                    f"Channel 'email' is not allowed for type '{notification_type}'"
                )
            
            if notification_type_obj.is_custom:
                if not template_name:
                    raise ValueError(f"For custom type '{notification_type}' a template name is required")
                
                template = NotificationTemplate.objects.filter(
                    notification_type=notification_type_obj,
                    channel=channel_obj,
                    name=template_name,
                    is_active=True
                ).first()
            else:
                template = NotificationTemplate.objects.filter(
                    notification_type=notification_type_obj,
                    channel=channel_obj,
                    is_active=True
                ).first()
            
            if not template:
                raise ValueError(
                    f"Template not found for type '{notification_type}' and channel 'email'"
                )
            
            engine = Engine()
            html_template = engine.from_string(template.html)
            rendered_html = html_template.render(Context(context))
            
            rendered_title = template.title
            if rendered_title:
                title_template = engine.from_string(rendered_title)
                rendered_title = title_template.render(Context(context))
            
            send_mail(
                subject=rendered_title or 'Notification',
                message='',
                html_message=rendered_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import sys
            if 'test' not in sys.modules:
                print(f"Error sending notification: {str(e)}")
            return False
