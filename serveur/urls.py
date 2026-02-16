# serveur/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Import pour la documentation automatique (optionnel)
try:
    from rest_framework.documentation import include_docs_urls
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # API principale (tous les endpoints) - inclut déjà api-auth
    path('api/', include('api.urls')),
    
    # URLs personnalisées pour l'admin (boutons d'action) - commenté
    # path('admin-custom/', include('api.admin_urls')),
    
    # Redirection de la racine vers l'API
    path('', RedirectView.as_view(url='/api/', permanent=False)),
]

# Documentation automatique de l'API
if DRF_AVAILABLE:
    urlpatterns += [
        path('api/docs/', include_docs_urls(title='Android Device Management API')),
    ]

# ⚠️ SUPPRIMEZ OU COMMENTEZ CES LIGNES (déjà dans api/urls.py)
# urlpatterns += [
#     path('api-auth/', include('rest_framework.urls')),
# ]

# Ajout des URLs pour les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # En développement, ajouter les outils de debug
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
    
    # Afficher les URLs disponibles en console
    print("\n" + "="*50)
    print("URLS DISPONIBLES EN MODE DEBUG")
    print("="*50)
    print("Admin: http://localhost:8000/admin/")
    print("API Root: http://localhost:8000/api/")
    print("API Docs: http://localhost:8000/api/docs/")
    print("="*50 + "\n")