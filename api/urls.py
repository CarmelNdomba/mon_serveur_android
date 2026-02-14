# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Création du routeur
router = DefaultRouter()
router.register(r'devices', views.DeviceViewSet, basename='device')

# Désactiver la racine automatique du router
router.include_root_view = False

# URLs personnalisées supplémentaires
extra_urlpatterns = [
    # COMMENTEZ CES LIGNES POUR L'INSTANT
    # path('stats/global/', views.global_stats, name='global-stats'),
    # path('stats/files/', views.files_global_stats, name='files-global-stats'),
    # path('export/devices/', views.export_devices_csv, name='export-devices'),
    # path('export/files/', views.export_files_csv, name='export-files'),
    # path('dashboard/', views.dashboard, name='dashboard'),
    # path('webhook/device/<str:android_id>/', views.device_webhook, name='device-webhook'),
]

urlpatterns = [
    # 1. La racine de l'API en PREMIER
    path('', views.APIRootView.as_view(), name='api-root'),
    
    # 2. URLs personnalisées (maintenant vides)
    path('', include(extra_urlpatterns)),
    
    # 3. Ensuite toutes les URLs du routeur
    path('', include(router.urls)),
    
    # 4. Authentification DRF
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]