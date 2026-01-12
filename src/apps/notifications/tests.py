from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.notifications.models.gradus_models import (
    Channel,
    Variable,
    NotificationType,
    NotificationTemplate
)
from apps.notifications.services.notification_sender import NotificationSender


class NotificationSenderTestCase(TestCase):
    """Tests for NotificationSender service"""
    
    def setUp(self):
        """Set up test data"""
        # Create channel
        self.channel = Channel.objects.create(
            title='email',
            allowed_tags=['p', 'b', 'i', 'a', 'br']
        )
        
        # Create variable
        self.variable = Variable.objects.create(title='title')
        
        # Create notification type
        self.notification_type = NotificationType.objects.create(
            title='new survey',
            is_custom=False
        )
        self.notification_type.channels.add(self.channel)
        self.notification_type.variables.add(self.variable)
        
        # Create template
        self.template = NotificationTemplate.objects.create(
            notification_type=self.notification_type,
            channel=self.channel,
            title='New Survey Available',
            html='<p>Hello! New survey: {{ title }}</p>'
        )
        
        self.sender = NotificationSender()
    
    def test_send_notification_success(self):
        """Test successful notification sending"""
        result = self.sender.send(
            notification_type='new survey',
            context={'title': 'Test Survey'},
            recipient='test@example.com'
        )
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'New Survey Available')
        # Check HTML message (email is sent as HTML)
        html_body = mail.outbox[0].alternatives[0][0] if mail.outbox[0].alternatives else mail.outbox[0].body
        self.assertIn('Test Survey', html_body)
    
    def test_send_notification_invalid_type(self):
        """Test sending with invalid notification type"""
        result = self.sender.send(
            notification_type='invalid_type',
            context={'title': 'Test'},
            recipient='test@example.com'
        )
        
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_notification_missing_template(self):
        """Test sending when template is missing"""
        # Delete template
        self.template.delete()
        
        result = self.sender.send(
            notification_type='new survey',
            context={'title': 'Test'},
            recipient='test@example.com'
        )
        
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_custom_notification(self):
        """Test sending custom notification"""
        # Create custom type
        custom_type = NotificationType.objects.create(
            title='custom',
            is_custom=True
        )
        custom_type.channels.add(self.channel)
        
        # Create custom template
        custom_template = NotificationTemplate.objects.create(
            notification_type=custom_type,
            channel=self.channel,
            name='welcome',
            html='<p>Welcome!</p>'
        )
        
        result = self.sender.send(
            notification_type='custom',
            context={},
            recipient='test@example.com',
            template_name='welcome'
        )
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
    
    def test_send_custom_notification_missing_name(self):
        """Test sending custom notification without template name"""
        custom_type = NotificationType.objects.create(
            title='custom',
            is_custom=True
        )
        custom_type.channels.add(self.channel)
        
        result = self.sender.send(
            notification_type='custom',
            context={},
            recipient='test@example.com'
        )
        
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)


class SendNotificationAPITestCase(TestCase):
    """Tests for SendNotification API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create channel
        self.channel = Channel.objects.create(
            title='email',
            allowed_tags=['p', 'b', 'i', 'a', 'br']
        )
        
        # Create variable
        self.variable = Variable.objects.create(title='title')
        
        # Create notification type
        self.notification_type = NotificationType.objects.create(
            title='new survey',
            is_custom=False
        )
        self.notification_type.channels.add(self.channel)
        self.notification_type.variables.add(self.variable)
        
        # Create template
        self.template = NotificationTemplate.objects.create(
            notification_type=self.notification_type,
            channel=self.channel,
            title='New Survey Available',
            html='<p>Hello! New survey: {{ title }}</p>'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_send_notification_api_success(self):
        """Test successful API call"""
        response = self.client.post(
            '/api/notifications/send/',
            {
                'notification_type': 'new survey',
                'context': {'title': 'Test Survey'},
                'recipient': 'user@example.com'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(len(mail.outbox), 1)
    
    def test_send_notification_api_unauthorized(self):
        """Test API call without authentication"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(
            '/api/notifications/send/',
            {
                'notification_type': 'new survey',
                'context': {'title': 'Test'},
                'recipient': 'user@example.com'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_send_notification_api_invalid_data(self):
        """Test API call with invalid data"""
        response = self.client.post(
            '/api/notifications/send/',
            {
                'notification_type': 'new survey',
                'context': {'title': 'Test'},
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_send_notification_api_invalid_email(self):
        """Test API call with invalid email"""
        response = self.client.post(
            '/api/notifications/send/',
            {
                'notification_type': 'new survey',
                'context': {'title': 'Test'},
                'recipient': 'invalid-email'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificationTemplateValidationTestCase(TestCase):
    """Tests for template validation"""
    
    def setUp(self):
        """Set up test data"""
        self.channel = Channel.objects.create(
            title='email',
            allowed_tags=['p', 'b', 'i', 'a', 'br']
        )
        
        self.variable = Variable.objects.create(title='title')
        
        self.notification_type = NotificationType.objects.create(
            title='new survey',
            is_custom=False
        )
        self.notification_type.channels.add(self.channel)
        self.notification_type.variables.add(self.variable)
    
    def test_template_with_allowed_tags(self):
        """Test template with allowed HTML tags"""
        template = NotificationTemplate(
            notification_type=self.notification_type,
            channel=self.channel,
            html='<p>Hello <b>{{ title }}</b>!</p>'
        )
        
        # Should not raise validation error
        try:
            template.full_clean()
            template.save()
            self.assertTrue(True)
        except Exception:
            self.fail("Template with allowed tags should be valid")
    
    def test_template_with_forbidden_tags(self):
        """Test template with forbidden HTML tags"""
        template = NotificationTemplate(
            notification_type=self.notification_type,
            channel=self.channel,
            html='<div>Hello <script>alert("xss")</script></div>'
        )
        
        with self.assertRaises(Exception):
            template.full_clean()
            template.save()
    
    def test_template_missing_required_variable(self):
        """Test template missing required variable"""
        template = NotificationTemplate(
            notification_type=self.notification_type,
            channel=self.channel,
            html='<p>Hello!</p>'
        )   
        
        with self.assertRaises(Exception):
            template.full_clean()
            template.save()
    
    def test_template_with_unknown_variable(self):
        """Test template with unknown variable"""
        template = NotificationTemplate(
            notification_type=self.notification_type,
            channel=self.channel,
            html='<p>{{ title }} {{ unknown }}</p>'
        )
        
        with self.assertRaises(Exception):
            template.full_clean()
            template.save()
