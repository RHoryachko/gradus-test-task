from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import LiveCheckView, NotificationTypeViewSet


router = DefaultRouter()
router.register(r'notification-types', NotificationTypeViewSet, basename='notificationtype')


urlpatterns = [
    path('live-check/', LiveCheckView.as_view(), name='live_check'),
] + router.urls