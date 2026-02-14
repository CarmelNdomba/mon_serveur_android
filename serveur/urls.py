"""
URL configuration for serveur project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    
    # API principale (tous les endpoints)
    path('api/', include('api.urls')),
    
    # URLs personnalisées pour l'admin (boutons d'action)
    path('admin-custom/', include('api.admin_urls')),
    
    # Redirection de la racine vers l'API (optionnel)
    path('', RedirectView.as_view(url='/api/', permanent=False)),
]

# Documentation automatique de l'API (si django-rest-framework est installé)
if DRF_AVAILABLE:
    urlpatterns += [
        path('api/docs/', include_docs_urls(title='Android Device Management API')),
    ]

# URLs pour l'authentification DRF (interface de login/logout)
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

# Ajout des URLs pour les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # En développement, ajouter les outils de debug (optionnel)
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
    
    # Afficher les URLs disponibles en console (pour debug)
    print("\n" + "="*50)
    print("URLS DISPONIBLES EN MODE DEBUG")
    print("="*50)
    print("Admin: http://localhost:8000/admin/")
    print("API Root: http://localhost:8000/api/")
    print("API Docs: http://localhost:8000/api/docs/")
    print("Admin Custom: http://localhost:8000/admin-custom/")
    print("="*50 + "\n")