from django.urls import path, include
from django.http import JsonResponse # Import necessário para o Health Check
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import OrderViewSet, ProductViewSet, CustomerViewSet

# Função simples para o health check 
def health_check(request):
    return JsonResponse({"status": "healthy"}, status=200)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('health/', health_check, name='health_check'),

    # Rotas da API
    path('', include(router.urls)),

    #  OpenAPI/Swagger
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]