from django.http import JsonResponse

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.notifications.models.gradus_models import NotificationType, NotificationTemplate
from apps.notifications.serializers import (
    NotificationTypeReadSerializer,
    NotificationTypeWriteSerializer,
    NotificationTemplateReadSerializer,
    NotificationTemplateWriteSerializer,
    SendNotificationSerializer
)
from apps.notifications.permissions import IsSuperUser
from apps.notifications.services.notification_sender import NotificationSender


@extend_schema(
    tags=['Health Check'],
    summary='Health check endpoint',
    description='Check if API is alive'
)
class LiveCheckView(APIView):
    def get(self, request):
        return JsonResponse({'status': 'ok'}, status=200)


@extend_schema_view(
    list=extend_schema(
        tags=['Notification Types'],
        summary='List notification types',
        description='Get list of all notification types'
    ),
    retrieve=extend_schema(
        tags=['Notification Types'],
        summary='Get notification type',
        description='Get details of a specific notification type'
    ),
    create=extend_schema(
        tags=['Notification Types'],
        summary='Create notification type',
        description='Create a new notification type (superuser only)'
    ),
    update=extend_schema(
        tags=['Notification Types'],
        summary='Update notification type',
        description='Update a notification type (superuser only)'
    ),
    partial_update=extend_schema(
        tags=['Notification Types'],
        summary='Partially update notification type',
        description='Partially update a notification type (superuser only)'
    ),
    destroy=extend_schema(
        tags=['Notification Types'],
        summary='Delete notification type',
        description='Delete a notification type (only custom types can be deleted)'
    ),
)
class NotificationTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NotificationType model
    """
    queryset = NotificationType.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return NotificationTypeReadSerializer
        return NotificationTypeWriteSerializer
    
    def get_queryset(self):
        queryset = NotificationType.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
    
    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        
        read_serializer = NotificationTypeReadSerializer(instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        
        read_serializer = NotificationTypeReadSerializer(instance)
        return Response(read_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_custom:
            return Response(
                {'error': 'Deletion of non-custom notification types is not allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=['Notification Templates'],
        summary='List notification templates',
        description='Get list of all notification templates'
    ),
    retrieve=extend_schema(
        tags=['Notification Templates'],
        summary='Get notification template',
        description='Get details of a specific notification template'
    ),
    create=extend_schema(
        tags=['Notification Templates'],
        summary='Create notification template',
        description='Create a new notification template (superuser only)'
    ),
    update=extend_schema(
        tags=['Notification Templates'],
        summary='Update notification template',
        description='Update a notification template (superuser only)'
    ),
    partial_update=extend_schema(
        tags=['Notification Templates'],
        summary='Partially update notification template',
        description='Partially update a notification template (superuser only)'
    ),
    destroy=extend_schema(
        tags=['Notification Templates'],
        summary='Delete notification template',
        description='Delete a notification template (only templates for custom types can be deleted)'
    ),
)
class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NotificationTemplate model
    """
    queryset = NotificationTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return NotificationTemplateReadSerializer
        return NotificationTemplateWriteSerializer
    
    def get_queryset(self):
        queryset = NotificationTemplate.objects.all()
        
        notification_type = self.request.query_params.get('notification_type', None)
        if notification_type:
            queryset = queryset.filter(notification_type__title=notification_type)
        
        channel = self.request.query_params.get('channel', None)
        if channel:
            queryset = queryset.filter(channel__title=channel)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        
        read_serializer = NotificationTemplateReadSerializer(instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        
        read_serializer = NotificationTemplateReadSerializer(instance)
        return Response(read_serializer.data)
    
    def destroy(self, request, *args, **kwargs):    
        instance = self.get_object()
        if not instance.notification_type.is_custom:
            return Response(
                {'error': 'Deletion of templates for non-custom notification types is not allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Notifications'],
    summary='Send notification',
    description='Send notification via email',
    request=SendNotificationSerializer,
    responses={
        200: {'description': 'Notification sent successfully'},
        400: {'description': 'Failed to send notification'},
    }
)
class SendNotificationView(APIView):
    """
    API endpoint for sending notifications
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sender = NotificationSender()
        success = sender.send(
            notification_type=serializer.validated_data['notification_type'],
            context=serializer.validated_data['context'],
            recipient=serializer.validated_data['recipient'],
            template_name=serializer.validated_data.get('template_name')
        )
        
        if success:
            return Response(
                {'message': 'Notification sent successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to send notification'},
                status=status.HTTP_400_BAD_REQUEST
            )