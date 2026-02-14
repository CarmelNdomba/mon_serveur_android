# api/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from django.db.models import Count, Q
from .models import Device
from .serializers import (
    DeviceRegistrationSerializer, 
    DeviceDetailSerializer, 
    DeviceHeartbeatSerializer,
    DeviceListSerializer,
    ServerCommandSerializer  # ← Nouveau serializer à créer
)

class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les appareils Android
    """
    queryset = Device.objects.all()
    
    def get_permissions(self):
        """
        Définit les permissions selon l'action
        - PUBLIC (téléphone → serveur) : register, heartbeat
        - ADMIN (serveur → téléphone) : send_command, pending_commands
        - ADMIN (gestion) : tout le reste
        """
        if self.action in ['register', 'heartbeat']:
            # Actions du téléphone vers le serveur (publiques)
            permission_classes = [AllowAny]
        elif self.action in ['send_command', 'pending_commands', 'regenerate_server_key']:
            # Actions du serveur vers le téléphone (admin seulement)
            permission_classes = [IsAdminUser]
        else:
            # Actions d'administration classiques
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Retourne le serializer approprié selon l'action
        """
        if self.action == 'register':
            return DeviceRegistrationSerializer
        elif self.action == 'heartbeat':
            return DeviceHeartbeatSerializer
        elif self.action == 'send_command':
            return ServerCommandSerializer
        elif self.action == 'list':
            return DeviceListSerializer
        elif self.action == 'retrieve':
            return DeviceDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return DeviceRegistrationSerializer
        return DeviceDetailSerializer
    
    def get_queryset(self):
        """
        Filtre les querysets si nécessaire
        """
        queryset = Device.objects.all()
        
        # Filtre par statut actif
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filtre par fabricant
        manufacturer = self.request.query_params.get('manufacturer', None)
        if manufacturer:
            queryset = queryset.filter(manufacturer__icontains=manufacturer)
        
        # Filtre par version Android
        android_version = self.request.query_params.get('android_version', None)
        if android_version:
            queryset = queryset.filter(android_version__icontains=android_version)
        
        # Filtre par modèle
        model = self.request.query_params.get('model', None)
        if model:
            queryset = queryset.filter(model__icontains=model)
        
        # Filtre par date (dernières 24h)
        last_24h = self.request.query_params.get('last_24h', None)
        if last_24h and last_24h.lower() == 'true':
            from datetime import timedelta
            queryset = queryset.filter(last_seen__gte=timezone.now() - timedelta(hours=24))
        
        return queryset.order_by('-last_seen')
    
    # ===== 1. ACTIONS DU TÉLÉPHONE VERS LE SERVEUR (PUBLIQUES) =====
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Endpoint PUBLIC pour l'enregistrement initial d'un appareil
        POST /api/devices/register/
        
        Le téléphone envoie ses infos et reçoit une device_key
        que le SERVEUR utilisera pour les futures communications.
        """
        android_id = request.data.get('androidId')
        
        if not android_id:
            return Response({
                'error': 'androidId est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'appareil existe déjà
        try:
            device = Device.objects.get(android_id=android_id)
            
            # Mettre à jour l'existant
            serializer = self.get_serializer(device, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Rafraîchir l'instance pour avoir les dernières données
            device.refresh_from_db()
            
            # Le téléphone reçoit la clé que le SERVEUR utilisera plus tard
            return Response({
                'status': 'updated',
                'message': 'Appareil mis à jour avec succès',
                'device_id': device.id,
                'server_key': device.device_key,  # 🔑 Clé pour le serveur
                'instructions': 'Cette clé sera utilisée par le SERVEUR pour vous contacter. Stockez-la pour vérifier l\'identité du serveur.'
            }, status=status.HTTP_200_OK)
            
        except Device.DoesNotExist:
            # Créer un nouvel appareil
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            device = serializer.save()
            
            return Response({
                'status': 'registered',
                'message': 'Appareil enregistré avec succès',
                'device_id': device.id,
                'server_key': device.device_key,  # 🔑 Clé pour le serveur
                'instructions': 'Cette clé sera utilisée par le SERVEUR pour vous contacter. Stockez-la pour vérifier l\'identité du serveur.'
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def heartbeat(self, request):
        """
        Endpoint PUBLIC pour les mises à jour périodiques
        POST /api/devices/heartbeat/
        
        Le téléphone envoie son état périodiquement.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        android_id = serializer.validated_data.get('androidId')
        
        try:
            device = Device.objects.get(android_id=android_id)
            
            # Mettre à jour les champs du heartbeat
            device.last_seen = timezone.now()
            device.is_active = True
            
            # Mise à jour conditionnelle des champs
            if 'battery_level' in serializer.validated_data and serializer.validated_data['battery_level'] is not None:
                device.battery_level = serializer.validated_data['battery_level']
            
            if 'is_charging' in serializer.validated_data and serializer.validated_data['is_charging'] is not None:
                device.is_charging = serializer.validated_data['is_charging']
            
            if 'available_storage' in serializer.validated_data and serializer.validated_data['available_storage'] is not None:
                device.available_storage = serializer.validated_data['available_storage']
            
            if 'network_type' in serializer.validated_data and serializer.validated_data['network_type']:
                device.network_type = serializer.validated_data['network_type']
            
            if 'is_roaming' in serializer.validated_data and serializer.validated_data['is_roaming'] is not None:
                device.is_roaming = serializer.validated_data['is_roaming']
            
            device.save()
            
            return Response({
                'status': 'ok',
                'message': 'Heartbeat reçu',
                'timestamp': timezone.now()
            }, status=status.HTTP_200_OK)
            
        except Device.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé. Veuillez d\'abord enregistrer l\'appareil.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # ===== 2. ACTIONS DU SERVEUR VERS LE TÉLÉPHONE (ADMIN SEULEMENT) =====
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def send_command(self, request, pk=None):
        """
        Endpoint ADMIN pour envoyer une commande à un téléphone spécifique
        POST /api/devices/{id}/send_command/
        
        Le serveur utilise cet endpoint pour envoyer des instructions
        Le téléphone doit vérifier que la commande vient bien du serveur
        en comparant avec la server_key qu'il a stockée.
        """
        device = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = serializer.validated_data.get('command')
        params = serializer.validated_data.get('params', {})
        priority = serializer.validated_data.get('priority', 'normal')
        expires_in = serializer.validated_data.get('expires_in')
        
        # TODO: Ici, implémentez votre système de file d'attente
        # Par exemple, créer une entrée dans une table Command
        # avec les champs : device, command, params, status, created_at, expires_at
        
        # Pour l'instant, on simule la mise en file d'attente
        command_id = f"cmd_{device.id}_{timezone.now().timestamp()}"
        
        return Response({
            'status': 'command_queued',
            'message': f'Commande {command} mise en file d\'attente',
            'command_id': command_id,
            'device': {
                'id': device.id,
                'android_id': device.android_id,
                'model': device.model,
            },
            'command': command,
            'params': params,
            'priority': priority,
            'expires_in': expires_in,
            'queued_at': timezone.now(),
            # ⚠️ Important : Le téléphone DEVRA vérifier que la commande vient bien du serveur
            'verification_required': True,
            'verification_method': 'Le téléphone doit vérifier que l\'expéditeur possède la server_key',
            'server_key_for_verification': device.device_key  # À utiliser côté téléphone pour vérifier
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def pending_commands(self, request, pk=None):
        """
        Endpoint ADMIN pour voir les commandes en attente pour un téléphone
        GET /api/devices/{id}/pending_commands/
        
        Le téléphone peut interroger cet endpoint régulièrement
        et doit vérifier l'authenticité avec sa server_key.
        """
        device = self.get_object()
        
        # TODO: Récupérer les commandes en attente depuis votre file d'attente
        # Pour l'instant, on retourne un exemple
        pending_commands = []
        
        # Si vous avez une table Command, vous feriez :
        # pending_commands = Command.objects.filter(
        #     device=device, 
        #     status='pending',
        #     expires_at__gt=timezone.now()
        # )
        
        return Response({
            'device_id': device.id,
            'device_android_id': device.android_id,
            'device_model': device.model,
            'pending_commands_count': len(pending_commands),
            'pending_commands': pending_commands,
            'verification_required': 'Le téléphone doit vérifier la signature du serveur',
            'server_key_for_verification': device.device_key
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def regenerate_server_key(self, request, pk=None):
        """
        Régénérer la clé serveur pour un appareil (en cas de compromission)
        POST /api/devices/{id}/regenerate_server_key/
        """
        device = self.get_object()
        old_key = device.device_key
        device.device_key = device.generate_key()
        device.save()
        
        return Response({
            'status': 'key_regenerated',
            'message': 'Clé serveur régénérée. La nouvelle clé doit être communiquée au téléphone.',
            'device_id': device.id,
            'android_id': device.android_id,
            'old_key': old_key[:10] + '...',  # Afficher seulement un aperçu
            'new_server_key': device.device_key,
            'old_key_invalidated': True,
            'instructions': 'Communiquez cette nouvelle clé au téléphone pour qu\'il mette à jour sa vérification.'
        }, status=status.HTTP_200_OK)
    
    # ===== 3. ACTIONS ADMIN CLASSIQUES (GESTION DES APPAREILS) =====
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Liste tous les appareils actifs
        GET /api/devices/active/
        """
        active_devices = Device.objects.filter(is_active=True)
        serializer = DeviceListSerializer(active_devices, many=True)
        return Response({
            'count': active_devices.count(),
            'devices': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques générales
        GET /api/devices/stats/
        """
        total = Device.objects.count()
        active = Device.objects.filter(is_active=True).count()
        inactive = total - active
        
        # Top fabricants
        top_manufacturers = Device.objects.values('manufacturer')\
            .exclude(manufacturer='')\
            .annotate(count=Count('manufacturer'))\
            .order_by('-count')[:5]
        
        # Top versions Android
        top_versions = Device.objects.values('android_version')\
            .exclude(android_version='Inconnue')\
            .annotate(count=Count('android_version'))\
            .order_by('-count')[:5]
        
        # Top modèles
        top_models = Device.objects.values('model')\
            .exclude(model='')\
            .annotate(count=Count('model'))\
            .order_by('-count')[:5]
        
        # Statistiques de root
        rooted_count = Device.objects.filter(is_rooted_score__gt=0.5).count()
        
        # Appareils vus aujourd'hui
        from datetime import timedelta
        today = timezone.now().date()
        seen_today = Device.objects.filter(last_seen__date=today).count()
        
        # Appareils vus cette semaine
        week_ago = timezone.now() - timedelta(days=7)
        seen_week = Device.objects.filter(last_seen__gte=week_ago).count()
        
        return Response({
            'total_devices': total,
            'active_devices': active,
            'inactive_devices': inactive,
            'seen_today': seen_today,
            'seen_this_week': seen_week,
            'rooted_devices': rooted_count,
            'emulator_count': Device.objects.filter(is_emulator=True).count(),
            'top_manufacturers': list(top_manufacturers),
            'top_android_versions': list(top_versions),
            'top_models': list(top_models),
            'timestamp': timezone.now()
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Désactiver un appareil
        POST /api/devices/{id}/deactivate/
        """
        device = self.get_object()
        device.is_active = False
        device.save()
        
        return Response({
            'status': 'deactivated',
            'device_id': device.id,
            'android_id': device.android_id,
            'message': 'Appareil désactivé avec succès'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Réactiver un appareil
        POST /api/devices/{id}/activate/
        """
        device = self.get_object()
        device.is_active = True
        device.last_seen = timezone.now()
        device.save()
        
        return Response({
            'status': 'activated',
            'device_id': device.id,
            'android_id': device.android_id,
            'message': 'Appareil réactivé avec succès'
        })
    
    @action(detail=True, methods=['get'])
    def info_complete(self, request, pk=None):
        """
        Récupère toutes les informations d'un appareil (version complète)
        GET /api/devices/{id}/info_complete/
        """
        device = self.get_object()
        
        # Utiliser le serializer de base pour avoir tous les champs
        serializer = DeviceRegistrationSerializer(device)
        
        # Ajouter des métadonnées supplémentaires
        data = serializer.data
        data['device_key'] = device.device_key
        data['created_at'] = device.created_at
        data['last_seen'] = device.last_seen
        data['is_active'] = device.is_active
        data['id'] = device.id
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Recherche avancée d'appareils
        GET /api/devices/search/?q=texte
        """
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({
                'error': 'La recherche doit contenir au moins 2 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        devices = Device.objects.filter(
            Q(android_id__icontains=query) |
            Q(model__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(brand__icontains=query) |
            Q(device_code__icontains=query)
        )[:20]  # Limiter à 20 résultats
        
        serializer = DeviceListSerializer(devices, many=True)
        return Response({
            'query': query,
            'count': devices.count(),
            'results': serializer.data
        })


# Vue simple pour la racine de l'API
class APIRootView(generics.GenericAPIView):
    """
    Vue pour la racine de l'API
    """
    permission_classes = [AllowAny]  # Public
    
    def get(self, request):
        return Response({
            'name': 'Android Device Management API',
            'version': '2.0',
            'description': 'API bidirectionnelle pour gérer les appareils Android',
            'public_endpoints': {
                'register': 'POST /api/devices/register/ - Enregistrer un appareil (reçoit une server_key)',
                'heartbeat': 'POST /api/devices/heartbeat/ - Mettre à jour l\'état',
            },
            'server_to_device_endpoints': {
                'send_command': 'POST /api/devices/{id}/send_command/ - Envoyer une commande à un appareil',
                'pending_commands': 'GET /api/devices/{id}/pending_commands/ - Voir les commandes en attente',
                'regenerate_key': 'POST /api/devices/{id}/regenerate_server_key/ - Régénérer la clé serveur',
            },
            'admin_endpoints': {
                'list': 'GET /api/devices/',
                'active': 'GET /api/devices/active/',
                'stats': 'GET /api/devices/stats/',
                'search': 'GET /api/devices/search/?q=texte',
                'detail': 'GET /api/devices/{id}/',
                'update': 'PUT /api/devices/{id}/',
                'partial_update': 'PATCH /api/devices/{id}/',
                'delete': 'DELETE /api/devices/{id}/',
                'deactivate': 'POST /api/devices/{id}/deactivate/',
                'activate': 'POST /api/devices/{id}/activate/',
                'info_complete': 'GET /api/devices/{id}/info_complete/',
            },
            'security_model': {
                'device_to_server': 'Public - Aucune authentification requise',
                'server_to_device': 'Authentification via server_key (vérifiée par le téléphone)',
                'admin_interface': 'Authentification via session Django (login admin requis)',
            },
            'documentation': 'https://github.com/votre-repo/docs',
            'support': 'support@example.com'
        })