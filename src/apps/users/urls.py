from django.urls import path
from apps.users.views import login_view, refresh_token_view


urlpatterns = [
    path('login/', login_view, name='login'),
    path('refresh/', refresh_token_view, name='refresh'),
]
