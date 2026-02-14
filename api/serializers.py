# api/serializers.py
from rest_framework import serializers
from .models import Device, FileList, FileItem, FileScanStats

# ===== SERIALIZERS POUR LES APPAREILS (EXISTANTS) =====

class DeviceRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'enregistrement des appareils
    Tous les champs sont optionnels sauf androidId
    """
    
    # On expose android_id comme androidId pour l'API
    androidId = serializers.CharField(source='android_id', required=True)
    
    class Meta:
        model = Device
        fields = [
            # Identifiants
            'androidId',
            
            # INFOS DE BASE
            'model',
            'manufacturer',
            'android_version',
            'brand',
            
            # INFOS MATÉRIELLES
            'hardware',
            'soc_manufacturer',
            'soc_model',
            'supported_abis',
            'board',
            'product',
            'device_code',
            
            # INFOS SYSTÈME
            'sdk_level',
            'build_id',
            'build_fingerprint',
            'build_type',
            'build_tags',
            'build_time',
            'security_patch',
            
            # MÉMOIRE ET STOCKAGE
            'total_ram',
            'total_storage',
            'available_storage',
            
            # ÉCRAN
            'screen_width',
            'screen_height',
            'screen_density',
            'screen_refresh_rate',
            
            # BATTERIE
            'battery_capacity',
            'battery_level',
            'is_charging',
            
            # RÉSEAU ET TÉLÉPHONIE
            'sim_operator',
            'sim_country',
            'sim_carrier_name',
            'network_operator',
            'network_country',
            'network_type',
            'is_roaming',
            'phone_count',
            'is_dual_sim',
            
            # LOCALISATION
            'language',
            'country',
            'timezone',
            'is_24hour_format',
            
            # SÉCURITÉ
            'is_rooted_score',
            'is_debuggable',
            'is_emulator',
            'has_verified_boot',
            'encryption_state',
            
            # CAPTEURS ET FONCTIONNALITÉS
            'has_camera',
            'has_nfc',
            'has_bluetooth',
            'has_fingerprint',
            'has_face_unlock',
            'has_ir_blaster',
            'has_compass',
            'has_gyroscope',
            'has_accelerometer',
            'camera_count',
            'camera_resolutions',
            
            # INFOS APPLICATION
            'app_version',
            'app_build_number',
            'is_first_install',
            'install_time',
            'update_time',
        ]
        extra_kwargs = {
            # Rendre tous les champs optionnels sauf androidId
            field: {'required': False, 'allow_null': True}
            for field in fields if field != 'androidId'
        }
    
    def validate_androidId(self, value):
        """Validation personnalisée pour androidId"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("androidId ne peut pas être vide")
        return value.strip()


class DeviceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher les détails d'un appareil (sans la clé)
    """
    androidId = serializers.CharField(source='android_id', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'androidId',
            'model',
            'manufacturer',
            'brand',
            'android_version',
            'sdk_level',
            'is_active',
            'created_at',
            'last_seen',
            'total_ram',
            'total_storage',
            'battery_capacity',
            'battery_level',
            'is_charging',
            'network_type',
            'has_nfc',
            'has_camera',
            'camera_count',
            'has_fingerprint',
            'language',
            'timezone',
            'is_rooted_score',
            'is_emulator',
        ]
        read_only_fields = fields  # Tous les champs sont en lecture seule


class DeviceHeartbeatSerializer(serializers.Serializer):
    """
    Serializer pour les heartbeats (mises à jour périodiques)
    """
    androidId = serializers.CharField(required=True)
    battery_level = serializers.IntegerField(min_value=0, max_value=100, required=False, allow_null=True)
    is_charging = serializers.BooleanField(required=False, allow_null=True)
    available_storage = serializers.IntegerField(required=False, allow_null=True)
    network_type = serializers.CharField(required=False, allow_blank=True)
    is_roaming = serializers.BooleanField(required=False, allow_null=True)
    location_lat = serializers.FloatField(required=False, allow_null=True)
    location_lng = serializers.FloatField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_androidId(self, value):
        if not value:
            raise serializers.ValidationError("androidId requis")
        return value.strip()


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des appareils (version légère)
    """
    androidId = serializers.CharField(source='android_id', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'androidId',
            'model',
            'manufacturer',
            'brand',
            'android_version',
            'is_active',
            'last_seen',
            'created_at',
        ]


# ===== SERIALIZERS POUR LES COMMANDES SERVEUR → TÉLÉPHONE =====

class ServerCommandSerializer(serializers.Serializer):
    """
    Serializer pour les commandes du serveur vers le téléphone
    Utilisé par l'admin pour envoyer des instructions aux appareils
    """
    COMMAND_CHOICES = [
        ('sync', 'Synchroniser les données'),
        ('update', 'Mettre à jour l\'application'),
        ('reboot', 'Redémarrer l\'appareil'),
        ('location', 'Demander la localisation'),
        ('photo', 'Prendre une photo'),
        ('notification', 'Afficher une notification'),
        ('backup', 'Lancer une sauvegarde'),
        ('factory_reset', 'Réinitialisation d\'usine'),
        ('lock', 'Verrouiller l\'appareil'),
        ('wipe', 'Effacer les données'),
        ('list_files', 'Lister tous les fichiers'),  # ← NOUVELLE COMMANDE
        ('custom', 'Commande personnalisée'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]
    
    command = serializers.ChoiceField(
        choices=COMMAND_CHOICES,
        required=True,
        help_text="Type de commande à exécuter"
    )
    
    params = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Paramètres supplémentaires pour la commande (format JSON)"
    )
    
    priority = serializers.ChoiceField(
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text="Priorité d'exécution"
    )
    
    expires_in = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=60,
        max_value=604800,  # 7 jours
        help_text="Temps d'expiration en secondes (60s à 7 jours)"
    )
    
    require_ack = serializers.BooleanField(
        default=True,
        help_text="Nécessite un accusé de réception du téléphone"
    )
    
    schedule_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Programmer l'exécution à une date ultérieure"
    )
    
    def validate_params(self, value):
        """
        Validation personnalisée des paramètres selon la commande
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les paramètres doivent être un objet JSON")
        return value
    
    def validate(self, data):
        """
        Validation croisée des champs
        """
        command = data.get('command')
        params = data.get('params', {})
        
        # Validations spécifiques selon la commande
        if command == 'notification' and 'message' not in params:
            raise serializers.ValidationError({
                'params': "Une commande 'notification' nécessite un champ 'message'"
            })
        
        if command == 'location' and 'accuracy' in params:
            accuracy = params['accuracy']
            if not isinstance(accuracy, int) or accuracy < 0 or accuracy > 100:
                raise serializers.ValidationError({
                    'params': "L'accuracy doit être un entier entre 0 et 100"
                })
        
        if command == 'sync' and 'folder' in params:
            if not isinstance(params['folder'], str):
                raise serializers.ValidationError({
                    'params': "Le champ 'folder' doit être une chaîne de caractères"
                })
        
        # === NOUVELLE VALIDATION POUR LIST_FILES ===
        if command == 'list_files':
            # Paramètres optionnels pour list_files
            if 'path' in params and not isinstance(params['path'], str):
                raise serializers.ValidationError({
                    'params': "Le champ 'path' doit être une chaîne de caractères"
                })
            
            if 'max_depth' in params and (not isinstance(params['max_depth'], int) or params['max_depth'] < 1):
                raise serializers.ValidationError({
                    'params': "max_depth doit être un entier >= 1"
                })
            
            if 'include_hidden' in params and not isinstance(params['include_hidden'], bool):
                raise serializers.ValidationError({
                    'params': "include_hidden doit être un booléen"
                })
            
            if 'file_types' in params and not isinstance(params['file_types'], list):
                raise serializers.ValidationError({
                    'params': "file_types doit être une liste"
                })
            
            if 'min_size' in params and (not isinstance(params['min_size'], int) or params['min_size'] < 0):
                raise serializers.ValidationError({
                    'params': "min_size doit être un entier >= 0"
                })
            
            if 'generate_hashes' in params and not isinstance(params['generate_hashes'], bool):
                raise serializers.ValidationError({
                    'params': "generate_hashes doit être un booléen"
                })
        
        return data


class CommandResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse après envoi d'une commande
    """
    status = serializers.CharField()
    message = serializers.CharField()
    command_id = serializers.CharField()
    device = serializers.DictField()
    command = serializers.CharField()
    params = serializers.JSONField()
    priority = serializers.CharField()
    expires_in = serializers.IntegerField(allow_null=True)
    queued_at = serializers.DateTimeField()
    verification_required = serializers.BooleanField()
    verification_method = serializers.CharField()
    server_key_for_verification = serializers.CharField()


class PendingCommandsSerializer(serializers.Serializer):
    """
    Serializer pour la liste des commandes en attente
    """
    device_id = serializers.IntegerField()
    device_android_id = serializers.CharField()
    device_model = serializers.CharField()
    pending_commands_count = serializers.IntegerField()
    pending_commands = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    verification_required = serializers.CharField()
    server_key_for_verification = serializers.CharField()


class ServerKeyRegenerateSerializer(serializers.Serializer):
    """
    Serializer pour la régénération de clé serveur
    """
    status = serializers.CharField()
    message = serializers.CharField()
    device_id = serializers.IntegerField()
    android_id = serializers.CharField()
    old_key = serializers.CharField()
    new_server_key = serializers.CharField()
    old_key_invalidated = serializers.BooleanField()
    instructions = serializers.CharField()


# ===== NOUVEAUX SERIALIZERS POUR LA GESTION DES FICHIERS =====

class FileItemSerializer(serializers.ModelSerializer):
    """
    Serializer pour un fichier individuel
    """
    size_mb = serializers.SerializerMethodField()
    size_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = FileItem
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_size_mb(self, obj):
        """Taille en MB arrondie"""
        if obj.size_bytes:
            return round(obj.size_bytes / (1024 * 1024), 2)
        return 0
    
    def get_size_formatted(self, obj):
        """Taille formatée (o, Ko, Mo, Go)"""
        size = obj.size_bytes
        if size < 1024:
            return f"{size} o"
        elif size < 1024 ** 2:
            return f"{size/1024:.1f} Ko"
        elif size < 1024 ** 3:
            return f"{size/1024**2:.1f} Mo"
        else:
            return f"{size/1024**3:.2f} Go"


class FileListSerializer(serializers.ModelSerializer):
    """
    Serializer pour une liste de fichiers (sans les items)
    """
    device_info = serializers.SerializerMethodField()
    files_count = serializers.IntegerField(source='files.count', read_only=True)
    size_gb = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = FileList
        fields = [
            'id', 
            'scan_id', 
            'device_info', 
            'status',
            'total_files', 
            'total_size_bytes',
            'size_gb',
            'files_count',
            'scan_requested_at', 
            'scan_started_at',
            'scan_completed_at',
            'scan_duration_ms',
            'duration_formatted',
            'error_message',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_device_info(self, obj):
        """Informations résumées de l'appareil"""
        return {
            'id': obj.device.id,
            'android_id': obj.device.android_id,
            'model': obj.device.model,
            'manufacturer': obj.device.manufacturer,
            'android_version': obj.device.android_version
        }
    
    def get_size_gb(self, obj):
        """Taille totale en GB"""
        if obj.total_size_bytes:
            return round(obj.total_size_bytes / (1024 ** 3), 2)
        return 0
    
    def get_duration_formatted(self, obj):
        """Durée formatée"""
        if obj.scan_duration_ms:
            seconds = obj.scan_duration_ms / 1000
            if seconds < 60:
                return f"{seconds:.1f} secondes"
            elif seconds < 3600:
                minutes = seconds // 60
                secs = seconds % 60
                return f"{int(minutes)} min {int(secs)} s"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{int(hours)} h {int(minutes)} min"
        return "N/A"


class FileListDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour une liste de fichiers avec tous les détails
    """
    device_info = serializers.SerializerMethodField()
    files = FileItemSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    files_by_type = serializers.SerializerMethodField()
    size_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = FileList
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_device_info(self, obj):
        """Informations complètes de l'appareil"""
        return {
            'id': obj.device.id,
            'android_id': obj.device.android_id,
            'model': obj.device.model,
            'manufacturer': obj.device.manufacturer,
            'brand': obj.device.brand,
            'android_version': obj.device.android_version,
            'total_storage': obj.device.total_storage,
            'is_active': obj.device.is_active
        }
    
    def get_stats(self, obj):
        """Statistiques rapides par type de fichier"""
        from django.db.models import Count, Sum
        
        stats = obj.files.values('file_type').annotate(
            count=Count('id'),
            total_size=Sum('size_bytes')
        ).order_by('file_type')
        
        result = {}
        for stat in stats:
            result[stat['file_type']] = {
                'count': stat['count'],
                'size_bytes': stat['total_size'],
                'size_mb': round(stat['total_size'] / (1024 * 1024), 2) if stat['total_size'] else 0,
                'size_gb': round(stat['total_size'] / (1024 ** 3), 2) if stat['total_size'] else 0
            }
        return result
    
    def get_files_by_type(self, obj):
        """Liste des fichiers groupés par type (limité)"""
        result = {}
        for file_type in ['image', 'video', 'audio', 'document', 'apk']:
            files = obj.files.filter(file_type=file_type)[:10]
            if files.exists():
                result[file_type] = FileItemSerializer(files, many=True).data
        return result
    
    def get_size_gb(self, obj):
        """Taille totale en GB"""
        if obj.total_size_bytes:
            return round(obj.total_size_bytes / (1024 ** 3), 2)
        return 0


class FileUploadSerializer(serializers.Serializer):
    """
    Serializer pour l'upload de la liste des fichiers par le téléphone
    """
    scan_id = serializers.CharField(required=True)
    androidId = serializers.CharField(required=True)
    command_id = serializers.CharField(required=False, allow_blank=True)
    
    # Métadonnées du scan
    scan_started_at = serializers.IntegerField(required=True, help_text="Timestamp début scan (ms)")
    scan_completed_at = serializers.IntegerField(required=True, help_text="Timestamp fin scan (ms)")
    scan_duration_ms = serializers.IntegerField(required=False, allow_null=True)
    
    # Statistiques
    total_files = serializers.IntegerField(required=True, min_value=0)
    total_size_bytes = serializers.IntegerField(required=True, min_value=0)
    
    # Statut du scan
    status = serializers.ChoiceField(
        choices=['completed', 'partial', 'failed'],
        default='completed'
    )
    error_message = serializers.CharField(required=False, allow_blank=True)
    
    # La liste des fichiers
    files = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    
    def validate_androidId(self, value):
        """Validation de l'androidId"""
        if not value or not value.strip():
            raise serializers.ValidationError("androidId requis")
        return value.strip()
    
    def validate_files(self, value):
        """Validation de la liste des fichiers"""
        if not isinstance(value, list):
            raise serializers.ValidationError("files doit être une liste")
        
        # Limiter le nombre de fichiers pour éviter les abus
        if len(value) > 200000:  # 200k fichiers max
            raise serializers.ValidationError("Trop de fichiers (max 200000)")
        
        # Vérifier que chaque fichier a les champs minimum requis
        for i, file_data in enumerate(value):
            if 'path' not in file_data:
                raise serializers.ValidationError(f"Fichier #{i}: champ 'path' requis")
            if 'name' not in file_data:
                raise serializers.ValidationError(f"Fichier #{i}: champ 'name' requis")
            if 'size_bytes' not in file_data:
                raise serializers.ValidationError(f"Fichier #{i}: champ 'size_bytes' requis")
        
        return value


class FileScanStatsSerializer(serializers.ModelSerializer):
    """
    Serializer pour les statistiques agrégées
    """
    class Meta:
        model = FileScanStats
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class FileSearchSerializer(serializers.Serializer):
    """
    Serializer pour la recherche de fichiers
    """
    query = serializers.CharField(required=False, allow_blank=True)
    file_type = serializers.ChoiceField(
        choices=['image', 'video', 'audio', 'document', 'apk', 'all'],
        default='all',
        required=False
    )
    min_size = serializers.IntegerField(required=False, min_value=0)
    max_size = serializers.IntegerField(required=False, min_value=0)
    extension = serializers.CharField(required=False, allow_blank=True)
    device_id = serializers.IntegerField(required=False)
    hidden_only = serializers.BooleanField(default=False)
    limit = serializers.IntegerField(default=100, min_value=1, max_value=1000)


# ===== COMMANDE SPÉCIFIQUE POUR LIST_FILES =====

class ListFilesCommandSerializer(serializers.Serializer):
    """
    Serializer spécifique pour la commande list_files
    """
    path = serializers.CharField(
        default='/storage/emulated/0',
        help_text="Dossier de départ du scan"
    )
    max_depth = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Profondeur maximale de scan"
    )
    include_hidden = serializers.BooleanField(
        default=False,
        help_text="Inclure les fichiers cachés"
    )
    file_types = serializers.ListField(
        child=serializers.ChoiceField(choices=['image', 'video', 'audio', 'document', 'apk']),
        required=False,
        default=[],
        help_text="Types de fichiers à inclure (vide = tous)"
    )
    min_size = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Taille minimum en octets"
    )
    max_size = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Taille maximum en octets"
    )
    generate_hashes = serializers.BooleanField(
        default=False,
        help_text="Générer les hash MD5/SHA1"
    )
    scan_media_metadata = serializers.BooleanField(
        default=True,
        help_text="Scanner les métadonnées des médias"
    )
    
    def validate(self, data):
        """Validation croisée"""
        if data.get('min_size') and data.get('max_size'):
            if data['min_size'] > data['max_size']:
                raise serializers.ValidationError(
                    "min_size ne peut pas être supérieur à max_size"
                )
        return data


# ===== NOUVEAUX SERIALIZERS POUR L'INTERFACE ADMIN =====

class DeviceWithFilesSerializer(serializers.ModelSerializer):
    """
    Serializer pour un appareil avec ses derniers scans
    """
    androidId = serializers.CharField(source='android_id', read_only=True)
    last_scan = serializers.SerializerMethodField()
    scans_count = serializers.IntegerField(source='file_lists.count', read_only=True)
    total_files_scanned = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'androidId',
            'model',
            'manufacturer',
            'android_version',
            'is_active',
            'last_seen',
            'created_at',
            'scans_count',
            'total_files_scanned',
            'last_scan'
        ]
    
    def get_last_scan(self, obj):
        """Dernier scan de l'appareil"""
        last_scan = obj.file_lists.filter(status='completed').first()
        if last_scan:
            return {
                'scan_id': last_scan.scan_id,
                'date': last_scan.scan_completed_at,
                'total_files': last_scan.total_files,
                'total_size_gb': round(last_scan.total_size_bytes / (1024**3), 2)
            }
        return None
    
    def get_total_files_scanned(self, obj):
        """Total des fichiers scannés (tous scans confondus)"""
        from django.db.models import Sum
        result = obj.file_lists.filter(status='completed').aggregate(
            total=Sum('total_files')
        )
        return result['total'] or 0


class FileTypeSummarySerializer(serializers.Serializer):
    """
    Serializer pour le résumé par type de fichier
    """
    file_type = serializers.CharField()
    count = serializers.IntegerField()
    total_size_bytes = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    total_size_gb = serializers.FloatField()
    percentage = serializers.FloatField()


class StorageSummarySerializer(serializers.Serializer):
    """
    Serializer pour le résumé de stockage d'un appareil
    """
    device_id = serializers.IntegerField()
    device_name = serializers.CharField()
    total_capacity_gb = serializers.FloatField()
    used_gb = serializers.FloatField()
    free_gb = serializers.FloatField()
    usage_percentage = serializers.FloatField()
    files_count = serializers.IntegerField()
    by_type = FileTypeSummarySerializer(many=True)
    largest_files = FileItemSerializer(many=True)