from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    LiveCheckView,
    NotificationTypeViewSet,
    NotificationTemplateViewSet,
    SendNotificationView
)


router = DefaultRouter()
router.register(r'notification-types', NotificationTypeViewSet, basename='notificationtype')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notificationtemplate')


urlpatterns = [
    path('live-check/', LiveCheckView.as_view(), name='live_check'),
    path('send/', SendNotificationView.as_view(), name='send_notification'),
] + router.urls