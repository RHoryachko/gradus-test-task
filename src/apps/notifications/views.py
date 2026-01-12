from django.http import JsonResponse

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.notifications.models.gradus_models import NotificationType
from apps.notifications.serializers import (
    NotificationTypeReadSerializer,
    NotificationTypeWriteSerializer
)
from apps.notifications.permissions import IsSuperUser


class LiveCheckView(APIView):
    def get(self, request):
        return JsonResponse({'status': 'ok'}, status=200)


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