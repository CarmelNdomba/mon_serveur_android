# api/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import Device, FileList, FileItem, FileScanStats
from django.db import models  # 👈 AJOUTE CETTE LIGNE

class FileItemInline(admin.TabularInline):
    """
    Affichage des fichiers dans le détail d'un scan (limité à 50)
    """
    model = FileItem
    fields = ['name', 'file_type', 'extension', 'size_formatted', 'path_preview']
    readonly_fields = ['name', 'file_type', 'extension', 'size_formatted', 'path_preview']
    extra = 0
    max_num = 50
    can_delete = False
    can_add = False
    ordering = ['-size_bytes']
    
    def size_formatted(self, obj):
        """Taille formatée"""
        if obj.size_bytes < 1024:
            return f"{obj.size_bytes} o"
        elif obj.size_bytes < 1024**2:
            return f"{obj.size_bytes/1024:.1f} Ko"
        elif obj.size_bytes < 1024**3:
            return f"{obj.size_bytes/1024**2:.1f} Mo"
        else:
            return f"{obj.size_bytes/1024**3:.2f} Go"
    size_formatted.short_description = "Taille"
    
    def path_preview(self, obj):
        """Aperçu du chemin (tronqué)"""
        if len(obj.path) > 60:
            return obj.path[:57] + '...'
        return obj.path
    path_preview.short_description = "Chemin"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class FileListInline(admin.TabularInline):
    """
    Affichage des scans dans le détail d'un appareil
    """
    model = FileList
    fields = ['scan_id_short', 'status', 'total_files', 'total_size_display', 
              'scan_completed_at', 'view_scan_link', 'download_link']
    readonly_fields = ['scan_id_short', 'status', 'total_files', 'total_size_display',
                       'scan_completed_at', 'view_scan_link', 'download_link']
    extra = 0
    max_num = 10
    can_delete = False
    ordering = ['-created_at']
    
    def scan_id_short(self, obj):
        """ID du scan tronqué"""
        if len(obj.scan_id) > 25:
            return obj.scan_id[:22] + '...'
        return obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def total_size_display(self, obj):
        """Taille totale formatée"""
        size = obj.total_size_bytes
        if size < 1024**3:
            return f"{size/1024**2:.1f} Mo"
        else:
            return f"{size/1024**3:.2f} Go"
    total_size_display.short_description = "Taille totale"
    
    def view_scan_link(self, obj):
        """Lien vers le détail du scan"""
        if obj.id:
            url = reverse('admin:api_filelist_change', args=[obj.id])
            return format_html('<a href="{}">🔍 Voir</a>', url)
        return "-"
    view_scan_link.short_description = "Actions"
    
    def download_link(self, obj):
        """Lien pour télécharger le scan en JSON"""
        if obj.id:
            url = reverse('admin:api_filelist_download', args=[obj.id])
            return format_html('<a href="{}" style="color: #28a745;">⬇️ JSON</a>', url)
        return "-"
    download_link.short_description = "Export"
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Device
    """
    # Champs à afficher dans la liste
    list_display = [
        'id',
        'android_id_short',
        'manufacturer',
        'model',
        'android_version',
        'is_active',
        'last_seen_ago',
        'files_count',
        'actions_buttons'
    ]
    
    # Champs sur lesquels on peut cliquer pour voir les détails
    list_display_links = ['id', 'android_id_short']
    
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
    ordering = ['-last_seen']
    
    # Nombre d'éléments par page
    list_per_page = 25
    
    # Champs en lecture seule
    readonly_fields = [
        'device_key',
        'created_at',
        'last_seen',
        'id',
        'files_stats'
    ]
    
    # Actions personnalisées
    actions = [
        'activate_devices', 
        'deactivate_devices', 
        'mark_as_emulator',
        'request_file_list_action',
        'cleanup_old_scans_action'
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
        
        # Section 3: Statut et activité
        ('Statut', {
            'fields': [
                'is_active',
                ('created_at', 'last_seen'),
                'files_stats'
            ],
            'classes': ['wide']
        }),
        
        # Section 4: Matériel (repliable)
        ('Matériel', {
            'fields': [
                ('hardware', 'board'),
                ('soc_manufacturer', 'soc_model'),
                'supported_abis',
                ('product', 'device_code')
            ],
            'classes': ['collapse']
        }),
        
        # Section 5: Système (repliable)
        ('Système', {
            'fields': [
                ('build_id', 'build_fingerprint'),
                ('build_type', 'build_tags'),
                ('build_time', 'security_patch')
            ],
            'classes': ['collapse']
        }),
        
        # Section 6: Mémoire et stockage (repliable)
        ('Mémoire et stockage', {
            'fields': [
                ('total_ram', 'total_storage'),
                'available_storage'
            ],
            'classes': ['collapse']
        }),
        
        # Section 7: Écran (repliable)
        ('Écran', {
            'fields': [
                ('screen_width', 'screen_height'),
                ('screen_density', 'screen_refresh_rate')
            ],
            'classes': ['collapse']
        }),
        
        # Section 8: Batterie (repliable)
        ('Batterie', {
            'fields': [
                'battery_capacity',
                ('battery_level', 'is_charging')
            ],
            'classes': ['collapse']
        }),
        
        # Section 9: Réseau (repliable)
        ('Réseau et téléphonie', {
            'fields': [
                ('sim_operator', 'sim_country', 'sim_carrier_name'),
                ('network_operator', 'network_country'),
                ('network_type', 'is_roaming'),
                ('phone_count', 'is_dual_sim')
            ],
            'classes': ['collapse']
        }),
        
        # Section 10: Localisation (repliable)
        ('Localisation', {
            'fields': [
                ('language', 'country'),
                ('timezone', 'is_24hour_format')
            ],
            'classes': ['collapse']
        }),
        
        # Section 11: Sécurité (repliable)
        ('Sécurité', {
            'fields': [
                ('is_rooted_score', 'is_debuggable'),
                ('is_emulator', 'has_verified_boot'),
                'encryption_state'
            ],
            'classes': ['collapse']
        }),
        
        # Section 12: Capteurs (repliable)
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
        
        # Section 13: Application (repliable)
        ('Informations application', {
            'fields': [
                ('app_version', 'app_build_number'),
                ('is_first_install', 'install_time', 'update_time')
            ],
            'classes': ['collapse']
        }),
    ]
    
    # Intégration des scans dans la page de détail
    inlines = [FileListInline]
    
    def get_readonly_fields(self, request, obj=None):
        """Ajoute des champs readonly conditionnels"""
        if obj:  # En édition
            return self.readonly_fields + ['android_id']
        return self.readonly_fields
    
    def android_id_short(self, obj):
        """Android ID tronqué"""
        if len(obj.android_id) > 16:
            return obj.android_id[:13] + '...'
        return obj.android_id
    android_id_short.short_description = "Android ID"
    android_id_short.admin_order_field = 'android_id'
    
    def last_seen_ago(self, obj):
        """Dernière vue formatée"""
        from django.utils.timesince import timesince
        if obj.last_seen:
            return f"{timesince(obj.last_seen)}"
        return "Jamais"
    last_seen_ago.short_description = "Dernière connexion"
    last_seen_ago.admin_order_field = 'last_seen'
    
    def files_count(self, obj):
        """Nombre de scans de fichiers"""
        count = obj.file_lists.count()
        if count > 0:
            url = reverse('admin:api_filelist_changelist') + f'?device__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    files_count.short_description = "Scans"
    files_count.admin_order_field = 'file_lists_count'
    
    def files_stats(self, obj):
        """Statistiques des fichiers pour cet appareil"""
        last_scan = obj.file_lists.filter(status='completed').first()
        if not last_scan:
            return "Aucun scan disponible"
        
        stats = last_scan.files.aggregate(
            total=Count('id'),
            images=Count('id', filter=models.Q(file_type='image')),
            videos=Count('id', filter=models.Q(file_type='video')),
            total_size=Sum('size_bytes')
        )
        
        total_size_gb = stats['total_size'] / (1024**3) if stats['total_size'] else 0
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Dernier scan:</strong> {}<br>'
            '📁 Total: {} fichiers<br>'
            '🖼️ Images: {} | 🎬 Vidéos: {}<br>'
            '💾 Taille totale: {:.2f} Go'
            '</div>',
            last_scan.scan_completed_at.strftime('%d/%m/%Y %H:%M'),
            stats['total'],
            stats['images'],
            stats['videos'],
            total_size_gb
        )
    files_stats.short_description = "Statistiques fichiers"
    
    def actions_buttons(self, obj):
        """Boutons d'action dans la liste"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="{}" style="background: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">📁 Scans</a>'
            '<a class="button" href="{}" style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">📱 Demander</a>'
            '<a class="button" href="{}" style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px;">📊 Stats</a>'
            '</div>',
            reverse('admin:api_filelist_changelist') + f'?device__id__exact={obj.id}',
            reverse('admin-custom:device-request-files', args=[obj.id]),
            reverse('admin:api_device_file_stats', args=[obj.id])
        )
    actions_buttons.short_description = "Actions"
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            file_lists_count=Count('file_lists', distinct=True)
        )
        return queryset
    
    # Actions personnalisées
    
    def activate_devices(self, request, queryset):
        """Action pour activer les appareils sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ {updated} appareil(s) activé(s) avec succès.")
    activate_devices.short_description = "✅ Activer les appareils sélectionnés"
    
    def deactivate_devices(self, request, queryset):
        """Action pour désactiver les appareils sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"❌ {updated} appareil(s) désactivé(s) avec succès.")
    deactivate_devices.short_description = "❌ Désactiver les appareils sélectionnés"
    
    def mark_as_emulator(self, request, queryset):
        """Action pour marquer comme émulateur"""
        updated = queryset.update(is_emulator=True)
        self.message_user(request, f"🖥️ {updated} appareil(s) marqué(s) comme émulateur.")
    mark_as_emulator.short_description = "🖥️ Marquer comme émulateur"
    
    def request_file_list_action(self, request, queryset):
        """Action pour demander la liste des fichiers"""
        count = 0
        for device in queryset:
            if device.is_active:
                # TODO: Envoyer la commande
                count += 1
        self.message_user(request, f"📱 Demande de fichiers envoyée à {count} appareil(s).")
    request_file_list_action.short_description = "📱 Demander la liste des fichiers"
    
    def cleanup_old_scans_action(self, request, queryset):
        """Nettoyer les vieux scans (garder les 5 derniers)"""
        total_deleted = 0
        for device in queryset:
            deleted = FileList.cleanup_old_scans(device, keep_last=5)
            total_deleted += deleted
        self.message_user(request, f"🧹 {total_deleted} vieux scans supprimés.")
    cleanup_old_scans_action.short_description = "🧹 Nettoyer les vieux scans (garder 5)"


@admin.register(FileList)
class FileListAdmin(admin.ModelAdmin):
    """
    Administration des scans de fichiers
    """
    list_display = [
        'id',
        'scan_id_short',
        'device_info',
        'status_colored',
        'files_count_display',
        'total_size_display',
        'scan_date',
        'actions_buttons'
    ]
    
    list_filter = [
        'status',
        'created_at',
        'device__manufacturer',
        'device__model'
    ]
    
    search_fields = [
        'scan_id',
        'device__android_id',
        'device__model',
        'error_message'
    ]
    
    readonly_fields = [
        'scan_id',
        'device',
        'scan_requested_at',
        'scan_started_at',
        'scan_completed_at',
        'scan_duration_ms',
        'total_files',
        'total_size_bytes',
        'command_id',
        'status',
        'error_message',
        'created_at',
        'updated_at',
        'files_preview',
        'stats_summary'
    ]
    
    fieldsets = [
        ('Informations du scan', {
            'fields': ['scan_id', 'device', 'status', 'command_id']
        }),
        ('Métadonnées temporelles', {
            'fields': [
                ('scan_requested_at', 'scan_started_at'),
                ('scan_completed_at', 'scan_duration_ms')
            ]
        }),
        ('Statistiques', {
            'fields': [
                ('total_files', 'total_size_bytes'),
                'files_preview',
                'stats_summary'
            ]
        }),
        ('Erreurs', {
            'fields': ['error_message'],
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
    
    inlines = [FileItemInline]
    
    actions = ['download_as_json', 'delete_selected_scans']
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('device')
        queryset = queryset.prefetch_related('files')
        return queryset
    
    def scan_id_short(self, obj):
        """ID du scan tronqué"""
        if len(obj.scan_id) > 30:
            return obj.scan_id[:27] + '...'
        return obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def device_info(self, obj):
        """Informations de l'appareil"""
        return format_html(
            '{} {}<br><small style="color: #666;">{}</small>',
            obj.device.manufacturer,
            obj.device.model,
            obj.device.android_id[:10] + '...'
        )
    device_info.short_description = "Appareil"
    device_info.admin_order_field = 'device__manufacturer'
    
    def status_colored(self, obj):
        """Statut avec couleur"""
        colors = {
            'pending': '#ffc107',
            'scanning': '#17a2b8',
            'completed': '#28a745',
            'partial': '#fd7e14',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_colored.short_description = "Statut"
    status_colored.admin_order_field = 'status'
    
    def files_count_display(self, obj):
        """Nombre de fichiers formaté"""
        count = obj.files.count()
        return f"{count:,}".replace(',', ' ')
    files_count_display.short_description = "Fichiers"
    files_count_display.admin_order_field = 'total_files'
    
    def total_size_display(self, obj):
        """Taille totale formatée"""
        size = obj.total_size_bytes
        if size < 1024**3:
            return f"{size/1024**2:.1f} Mo"
        else:
            return f"{size/1024**3:.2f} Go"
    total_size_display.short_description = "Taille totale"
    total_size_display.admin_order_field = 'total_size_bytes'
    
    def scan_date(self, obj):
        """Date du scan formatée"""
        if obj.scan_completed_at:
            return obj.scan_completed_at.strftime('%d/%m/%Y %H:%M')
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    scan_date.short_description = "Date scan"
    scan_date.admin_order_field = 'scan_completed_at'
    
    def files_preview(self, obj):
        """Aperçu des types de fichiers"""
        from django.db.models import Count
        
        stats = obj.files.values('file_type').annotate(count=Count('id'))
        
        html = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
        icons = {
            'image': '🖼️',
            'video': '🎬',
            'audio': '🎵',
            'document': '📄',
            'apk': '📱',
            'archive': '🗜️',
            'other': '📁'
        }
        
        for stat in stats:
            icon = icons.get(stat['file_type'], '📁')
            html += f'<div style="background: #e9ecef; padding: 5px 10px; border-radius: 3px;">{icon} {stat["file_type"]}: {stat["count"]}</div>'
        
        html += '</div>'
        return format_html(html)
    files_preview.short_description = "Aperçu par type"
    
    def stats_summary(self, obj):
        """Résumé des statistiques"""
        if hasattr(obj, 'stats'):
            stats = obj.stats
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Images:</strong> {} ({} Mo)<br>'
                '<strong>Vidéos:</strong> {} ({} Mo)<br>'
                '<strong>Audio:</strong> {} ({} Mo)<br>'
                '<strong>Documents:</strong> {} ({} Mo)<br>'
                '<strong>APK:</strong> {} ({} Mo)<br>'
                '<strong>Fichiers cachés:</strong> {}'
                '</div>',
                stats.images_count, stats.images_size / 1024**2,
                stats.videos_count, stats.videos_size / 1024**2,
                stats.audio_count, stats.audio_size / 1024**2,
                stats.documents_count, stats.documents_size / 1024**2,
                stats.apks_count, stats.apks_size / 1024**2,
                stats.hidden_files_count
            )
        return "Statistiques non disponibles"
    stats_summary.short_description = "Résumé détaillé"
    
    def actions_buttons(self, obj):
        """Boutons d'action"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="{}" target="_blank" style="background: #28a745; color: white;">⬇️ JSON</a>'
            '<a class="button" href="{}" style="background: #17a2b8; color: white;">🔍 Fichiers</a>'
            '</div>',
            reverse('admin-custom:scan-download', args=[obj.id]),
            reverse('admin:api_fileitem_changelist') + f'?file_list__id__exact={obj.id}'
        )
    actions_buttons.short_description = "Actions"
    
    def download_as_json(self, request, queryset):
        """Exporter les scans en JSON"""
        count = queryset.count()
        self.message_user(request, f"📥 Export de {count} scan(s) demandé. Utilisez le bouton individuel pour télécharger.")
    download_as_json.short_description = "📥 Exporter en JSON"
    
    def delete_selected_scans(self, request, queryset):
        """Supprimer les scans sélectionnés"""
        file_count = sum(scan.files.count() for scan in queryset)
        scan_count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ {scan_count} scan(s) et {file_count} fichier(s) supprimés.")
    delete_selected_scans.short_description = "🗑️ Supprimer les scans sélectionnés"


@admin.register(FileItem)
class FileItemAdmin(admin.ModelAdmin):
    """
    Administration des fichiers individuels
    """
    list_display = [
        'name_truncated',
        'file_type_icon',
        'extension',
        'size_display',
        'device_model',
        'scan_date_short',
        'actions'
    ]
    
    list_filter = [
        'file_type',
        'extension',
        'is_hidden',
        'is_directory',
        'file_list__device__manufacturer'
    ]
    
    search_fields = [
        'name',
        'path',
        'file_list__device__android_id',
        'file_list__device__model'
    ]
    
    readonly_fields = [
        'file_list',
        'path',
        'name',
        'extension',
        'size_bytes',
        'last_modified',
        'last_accessed',
        'created_at_time',
        'file_type',
        'mime_type',
        'is_readable',
        'is_writable',
        'is_hidden',
        'is_directory',
        'md5_hash',
        'sha1_hash',
        'media_width',
        'media_height',
        'media_duration_ms',
        'media_date_taken',
        'media_gps_lat',
        'media_gps_lng',
        'apk_package_name',
        'apk_version_code',
        'apk_version_name',
        'apk_min_sdk',
        'created_at'
    ]
    
    fieldsets = [
        ('Fichier', {
            'fields': ['name', 'path', 'extension', 'size_bytes']
        }),
        ('Classification', {
            'fields': ['file_type', 'mime_type', 'is_directory', 'is_hidden']
        }),
        ('Dates', {
            'fields': ['last_modified', 'last_accessed', 'created_at_time']
        }),
        ('Médias', {
            'fields': [
                ('media_width', 'media_height'),
                'media_duration_ms',
                'media_date_taken',
                ('media_gps_lat', 'media_gps_lng')
            ],
            'classes': ['collapse']
        }),
        ('Application (APK)', {
            'fields': [
                'apk_package_name',
                ('apk_version_code', 'apk_version_name'),
                'apk_min_sdk'
            ],
            'classes': ['collapse']
        }),
        ('Intégrité', {
            'fields': ['md5_hash', 'sha1_hash'],
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ['file_list', 'created_at']
        }),
    ]
    
    actions = ['show_path', 'mark_as_hidden', 'mark_as_visible']
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('file_list__device')
        return queryset
    
    def name_truncated(self, obj):
        """Nom tronqué"""
        if len(obj.name) > 40:
            return obj.name[:37] + '...'
        return obj.name
    name_truncated.short_description = "Nom"
    name_truncated.admin_order_field = 'name'
    
    def file_type_icon(self, obj):
        """Icône selon le type"""
        icons = {
            'image': '🖼️',
            'video': '🎬',
            'audio': '🎵',
            'document': '📄',
            'apk': '📱',
            'archive': '🗜️',
            'database': '🗄️',
            'log': '📝',
        }
        return icons.get(obj.file_type, '📁')
    file_type_icon.short_description = " "
    
    def size_display(self, obj):
        """Taille formatée"""
        if obj.size_bytes < 1024:
            return f"{obj.size_bytes} o"
        elif obj.size_bytes < 1024**2:
            return f"{obj.size_bytes/1024:.1f} Ko"
        elif obj.size_bytes < 1024**3:
            return f"{obj.size_bytes/1024**2:.1f} Mo"
        else:
            return f"{obj.size_bytes/1024**3:.2f} Go"
    size_display.short_description = "Taille"
    size_display.admin_order_field = 'size_bytes'
    
    def device_model(self, obj):
        """Modèle de l'appareil"""
        return f"{obj.file_list.device.manufacturer} {obj.file_list.device.model}"
    device_model.short_description = "Appareil"
    device_model.admin_order_field = 'file_list__device__model'
    
    def scan_date_short(self, obj):
        """Date du scan formatée"""
        if obj.file_list.scan_completed_at:
            return obj.file_list.scan_completed_at.strftime('%d/%m/%Y')
        return obj.file_list.created_at.strftime('%d/%m/%Y')
    scan_date_short.short_description = "Date scan"
    scan_date_short.admin_order_field = 'file_list__scan_completed_at'
    
    def actions(self, obj):
        """Boutons d'action"""
        return format_html(
            '<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 2px 5px; border-radius: 3px; text-decoration: none;">🔍</a>',
            reverse('admin:api_fileitem_change', args=[obj.id])
        )
    actions.short_description = " "
    
    def show_path(self, request, queryset):
        """Afficher le chemin des fichiers sélectionnés"""
        for obj in queryset[:10]:  # Limiter à 10
            self.message_user(request, f"📁 {obj.path}")
    show_path.short_description = "🔍 Afficher les chemins"
    
    def mark_as_hidden(self, request, queryset):
        """Marquer comme caché"""
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f"👁️ {updated} fichier(s) marqué(s) comme cachés.")
    mark_as_hidden.short_description = "👁️ Marquer comme caché"
    
    def mark_as_visible(self, request, queryset):
        """Marquer comme visible"""
        updated = queryset.update(is_hidden=False)
        self.message_user(request, f"👁️ {updated} fichier(s) marqué(s) comme visibles.")
    mark_as_visible.short_description = "👁️ Marquer comme visible"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FileScanStats)
class FileScanStatsAdmin(admin.ModelAdmin):
    """
    Administration des statistiques de scans
    """
    list_display = [
        'id',
        'scan_info',
        'images_stats',
        'videos_stats',
        'total_size_display',
        'created_at'
    ]
    
    list_filter = ['created_at']
    
    readonly_fields = [field.name for field in FileScanStats._meta.fields]
    
    def scan_info(self, obj):
        """Informations du scan"""
        return format_html(
            '{}<br><small>Scan #{}</small>',
            obj.file_list.device,
            obj.file_list.id
        )
    scan_info.short_description = "Scan"
    
    def images_stats(self, obj):
        """Statistiques des images"""
        return f"{obj.images_count} ({obj.images_size/1024**2:.1f} Mo)"
    images_stats.short_description = "Images"
    
    def videos_stats(self, obj):
        """Statistiques des vidéos"""
        return f"{obj.videos_count} ({obj.videos_size/1024**2:.1f} Mo)"
    videos_stats.short_description = "Vidéos"
    
    def total_size_display(self, obj):
        """Taille totale formatée"""
        total = (obj.images_size + obj.videos_size + obj.audio_size + 
                obj.documents_size + obj.apks_size + obj.archives_size)
        return f"{total/1024**3:.2f} Go"
    total_size_display.short_description = "Total"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False