from django.urls import path

from .views import LiveCheckView


urlpatterns = [
    path('live-check/', LiveCheckView.as_view(), name='live_check'),
]