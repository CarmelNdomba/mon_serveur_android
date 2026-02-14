

# Register your models here.
# api/admin.py
from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Device
    """
    # Champs à afficher dans la liste
    list_display = [
        'id',
        'android_id',
        'manufacturer',
        'model',
        'android_version',
        'is_active',
        'last_seen',
        'created_at'
    ]
    
    # Champs sur lesquels on peut cliquer pour voir les détails
    list_display_links = ['id', 'android_id']
    
    # Champs utilisés pour les filtres latéraux
    list_filter = [
        'manufacturer',
        'android_version',
        'is_active',
        'has_nfc',
        'has_camera',
        'has_fingerprint',
        'is_emulator',
        'created_at',
        'last_seen'
    ]
    
    # Champs pour la recherche
    search_fields = [
        'android_id',
        'model',
        'manufacturer',
        'brand',
        'device_code',
        'build_id'
    ]
    
    # Ordre par défaut
    ordering = ['-created_at']
    
    # Nombre d'éléments par page
    list_per_page = 25
    
    # Champs en lecture seule
    readonly_fields = [
        'device_key',
        'created_at',
        'last_seen',
        'id'
    ]
    
    # Organisation des champs dans le formulaire de détail
    fieldsets = [
        # Section 1: Identifiants
        ('Identifiants', {
            'fields': [
                'id',
                'android_id',
                'device_key'
            ],
            'classes': ['wide']
        }),
        
        # Section 2: Informations de base
        ('Informations de base', {
            'fields': [
                'manufacturer',
                'model',
                'brand',
                'android_version',
                'sdk_level'
            ],
            'classes': ['wide']
        }),
        
        # Section 3: Matériel
        ('Matériel', {
            'fields': [
                ('hardware', 'board'),
                ('soc_manufacturer', 'soc_model'),
                'supported_abis',
                ('product', 'device_code')
            ],
            'classes': ['collapse']  # Section repliable
        }),
        
        # Section 4: Système
        ('Système', {
            'fields': [
                ('build_id', 'build_fingerprint'),
                ('build_type', 'build_tags'),
                ('build_time', 'security_patch')
            ],
            'classes': ['collapse']
        }),
        
        # Section 5: Mémoire et stockage
        ('Mémoire et stockage', {
            'fields': [
                ('total_ram', 'total_storage'),
                'available_storage'
            ],
            'classes': ['collapse']
        }),
        
        # Section 6: Écran
        ('Écran', {
            'fields': [
                ('screen_width', 'screen_height'),
                ('screen_density', 'screen_refresh_rate')
            ],
            'classes': ['collapse']
        }),
        
        # Section 7: Batterie
        ('Batterie', {
            'fields': [
                'battery_capacity',
                ('battery_level', 'is_charging')
            ],
            'classes': ['collapse']
        }),
        
        # Section 8: Réseau
        ('Réseau et téléphonie', {
            'fields': [
                ('sim_operator', 'sim_country', 'sim_carrier_name'),
                ('network_operator', 'network_country'),
                ('network_type', 'is_roaming'),
                ('phone_count', 'is_dual_sim')
            ],
            'classes': ['collapse']
        }),
        
        # Section 9: Localisation
        ('Localisation', {
            'fields': [
                ('language', 'country'),
                ('timezone', 'is_24hour_format')
            ],
            'classes': ['collapse']
        }),
        
        # Section 10: Sécurité
        ('Sécurité', {
            'fields': [
                ('is_rooted_score', 'is_debuggable'),
                ('is_emulator', 'has_verified_boot'),
                'encryption_state'
            ],
            'classes': ['collapse']
        }),
        
        # Section 11: Capteurs
        ('Capteurs et fonctionnalités', {
            'fields': [
                ('has_camera', 'camera_count', 'camera_resolutions'),
                ('has_nfc', 'has_bluetooth'),
                ('has_fingerprint', 'has_face_unlock'),
                ('has_ir_blaster', 'has_compass'),
                ('has_gyroscope', 'has_accelerometer')
            ],
            'classes': ['collapse']
        }),
        
        # Section 12: Application
        ('Informations application', {
            'fields': [
                ('app_version', 'app_build_number'),
                ('is_first_install', 'install_time', 'update_time')
            ],
            'classes': ['collapse']
        }),
        
        # Section 13: Métadonnées
        ('Métadonnées', {
            'fields': [
                ('is_active', 'created_at'),
                'last_seen'
            ],
            'classes': ['wide']
        }),
    ]
    
    # Actions personnalisées dans la liste
    actions = ['activate_devices', 'deactivate_devices', 'mark_as_emulator']
    
    def activate_devices(self, request, queryset):
        """Action pour activer les appareils sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} appareil(s) activé(s) avec succès.")
    activate_devices.short_description = "Activer les appareils sélectionnés"
    
    def deactivate_devices(self, request, queryset):
        """Action pour désactiver les appareils sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} appareil(s) désactivé(s) avec succès.")
    deactivate_devices.short_description = "Désactiver les appareils sélectionnés"
    
    def mark_as_emulator(self, request, queryset):
        """Action pour marquer comme émulateur"""
        updated = queryset.update(is_emulator=True)
        self.message_user(request, f"{updated} appareil(s) marqué(s) comme émulateur.")
    mark_as_emulator.short_description = "Marquer comme émulateur"


# Optionnel : Configuration plus simple si tu préfères
class DeviceAdminSimple(admin.ModelAdmin):
    """
    Version simplifiée de l'admin (à utiliser si tu préfères)
    """
    list_display = ['android_id', 'manufacturer', 'model', 'android_version', 'is_active', 'last_seen']
    list_filter = ['manufacturer', 'android_version', 'is_active']
    search_fields = ['android_id', 'model', 'manufacturer']
    readonly_fields = ['device_key', 'created_at', 'last_seen']
    
    fieldsets = [
        ('Informations de base', {
            'fields': ['android_id', 'manufacturer', 'model', 'android_version']
        }),
        ('Statut', {
            'fields': ['is_active', 'created_at', 'last_seen', 'device_key']
        }),
        ('Batterie', {
            'fields': ['battery_level', 'is_charging']
        }),
        ('Réseau', {
            'fields': ['network_type', 'is_roaming']
        }),
    ]