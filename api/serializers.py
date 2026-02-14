# api/serializers.py
from rest_framework import serializers
from .models import Device

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
            'androidId',  # Utilise le format camelCase comme dans l'enregistrement
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


# ===== NOUVEAU SERIALIZER POUR LES COMMANDES SERVEUR → TÉLÉPHONE =====

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