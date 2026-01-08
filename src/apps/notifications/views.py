from django.http import JsonResponse
from rest_framework.views import APIView

# Create your views here.
class LiveCheckView(APIView):
    def get(self, request):
        return JsonResponse({'status': 'ok'}, status=200)