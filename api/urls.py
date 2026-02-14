# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Création du routeur
router = DefaultRouter()
router.register(r'devices', views.DeviceViewSet, basename='device')

# Désactiver la racine automatique du router
router.include_root_view = False

urlpatterns = [
    # 1. La racine de l'API en PREMIER
    path('', views.APIRootView.as_view(), name='api-root'),
    
    # 2. Ensuite toutes les URLs du routeur
    path('', include(router.urls)),
]