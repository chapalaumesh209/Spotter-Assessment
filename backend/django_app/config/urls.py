from django.urls import path
from fuel_optimizer.views import RouteCalculateView, HealthCheckView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='root'),
    path('api/v1/health', HealthCheckView.as_view(), name='health'),
    path('api/v1/route', RouteCalculateView.as_view(), name='calculate_route_v1'),
    path('api/route', RouteCalculateView.as_view(), name='calculate_route_short'),
]
