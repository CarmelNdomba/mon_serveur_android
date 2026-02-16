# api/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import Device, FileList, FileItem, FileScanStats


class FileItemInline(admin.TabularInline):
    """Affichage des fichiers dans le détail d'un scan"""
    model = FileItem
    fields = ['name', 'file_type', 'size_formatted', 'path_preview']
    readonly_fields = ['name', 'file_type', 'size_formatted', 'path_preview']
    extra = 0
    max_num = 30
    can_delete = False
    can_add = False
    ordering = ['-size_bytes']
    
    def size_formatted(self, obj):
        """Taille formatée lisible"""
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
        """Aperçu du chemin tronqué"""
        return obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
    path_preview.short_description = "Chemin"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class FileListInline(admin.TabularInline):
    """Affichage des scans dans le détail d'un appareil"""
    model = FileList
    fields = ['scan_id_short', 'status', 'total_files', 'total_size_display', 'created_at', 'view_scan_link']
    readonly_fields = ['scan_id_short', 'status', 'total_files', 'total_size_display', 'created_at', 'view_scan_link']
    extra = 0
    max_num = 5
    can_delete = False
    ordering = ['-created_at']
    
    def scan_id_short(self, obj):
        """ID du scan tronqué"""
        return obj.scan_id[:20] + '...' if len(obj.scan_id) > 20 else obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def total_size_display(self, obj):
        """Taille totale formatée"""
        size = obj.total_size_bytes
        if size < 1024**3:
            return f"{size/1024**2:.1f} Mo"
        return f"{size/1024**3:.2f} Go"
    total_size_display.short_description = "Taille"
    
    def view_scan_link(self, obj):
        """Lien vers le détail du scan"""
        if obj.id:
            url = reverse('admin:api_filelist_change', args=[obj.id])
            return format_html('<a href="{}">🔍 Voir détails</a>', url)
        return "-"
    view_scan_link.short_description = "Actions"
    
    def has_add_permission(self, request, obj=None):
        return False


class DeviceFilesInline(admin.TabularInline):
    """Affiche les fichiers récents directement dans l'appareil"""
    model = FileItem
    fields = ['name', 'file_type', 'size_formatted', 'scan_date', 'view_file_link']
    readonly_fields = ['name', 'file_type', 'size_formatted', 'scan_date', 'view_file_link']
    extra = 0
    max_num = 10
    can_delete = False
    can_add = False
    ordering = ['-file_list__created_at']
    
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
    
    def scan_date(self, obj):
        """Date du scan"""
        return obj.file_list.created_at.strftime('%d/%m/%Y %H:%M')
    scan_date.short_description = "Date scan"
    
    def view_file_link(self, obj):
        """Lien vers le détail du fichier"""
        if obj.id:
            url = reverse('admin:api_fileitem_change', args=[obj.id])
            return format_html('<a href="{}">🔍 Voir</a>', url)
        return "-"
    view_file_link.short_description = "Actions"
    
    def get_queryset(self, request):
        """Limiter aux 10 fichiers les plus récents"""
        return super().get_queryset(request).select_related('file_list').order_by('-file_list__created_at')[:10]
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Administration des appareils - Version complète avec liens vers fichiers"""
    
    list_display = [
        'id',
        'android_id_short',
        'manufacturer',
        'model',
        'android_version',
        'is_active',
        'last_seen_ago',
        'scans_count',
        'files_count',
        'view_files_link'
    ]
    
    list_display_links = ['id', 'android_id_short']
    
    list_filter = [
        'manufacturer',
        'android_version',
        'is_active',
        'has_camera',
        'has_nfc',
        'is_emulator',
        'created_at',
        'last_seen'
    ]
    
    search_fields = [
        'android_id',
        'model',
        'manufacturer',
        'brand',
        'device_code'
    ]
    
    ordering = ['-last_seen']
    list_per_page = 25
    
    readonly_fields = [
        'device_key',
        'created_at',
        'last_seen',
        'id',
        'storage_summary'
    ]
    
    fieldsets = [
        ('Identifiants', {
            'fields': ['id', 'android_id', 'device_key'],
            'classes': ['wide']
        }),
        ('Informations de base', {
            'fields': ['manufacturer', 'model', 'brand', 'android_version', 'sdk_level'],
            'classes': ['wide']
        }),
        ('Statut', {
            'fields': ['is_active', ('created_at', 'last_seen'), 'storage_summary'],
            'classes': ['wide']
        }),
        ('Matériel (repliable)', {
            'fields': ['hardware', 'board', 'soc_manufacturer', 'soc_model', 'supported_abis'],
            'classes': ['collapse']
        }),
        ('Mémoire', {
            'fields': [('total_ram', 'total_storage'), 'available_storage'],
            'classes': ['collapse']
        }),
        ('Batterie', {
            'fields': ['battery_capacity', ('battery_level', 'is_charging')],
            'classes': ['collapse']
        }),
        ('Réseau', {
            'fields': ['network_type', 'is_roaming', 'sim_operator', 'sim_country'],
            'classes': ['collapse']
        }),
        ('Sécurité', {
            'fields': ['is_rooted_score', 'is_emulator', 'has_verified_boot'],
            'classes': ['collapse']
        }),
        ('Capteurs', {
            'fields': ['has_camera', 'has_nfc', 'has_bluetooth', 'has_fingerprint'],
            'classes': ['collapse']
        }),
    ]
    
    actions = [
        'activate_devices',
        'deactivate_devices',
        'mark_as_emulator',
        'request_file_list_action'
    ]
    
    inlines = [FileListInline, DeviceFilesInline]  # Les deux inlines : scans et fichiers récents
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['android_id']
        return self.readonly_fields
    
    def android_id_short(self, obj):
        return obj.android_id[:10] + '...' if len(obj.android_id) > 10 else obj.android_id
    android_id_short.short_description = "Android ID"
    android_id_short.admin_order_field = 'android_id'
    
    def last_seen_ago(self, obj):
        from django.utils.timesince import timesince
        if obj.last_seen:
            return f"{timesince(obj.last_seen)}"
        return "Jamais"
    last_seen_ago.short_description = "Dernière connexion"
    last_seen_ago.admin_order_field = 'last_seen'
    
    def scans_count(self, obj):
        count = obj.file_lists.count()
        if count > 0:
            url = reverse('admin:api_filelist_changelist') + f'?device__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    scans_count.short_description = "Scans"
    scans_count.admin_order_field = 'file_lists_count'
    
    def files_count(self, obj):
        """Nombre total de fichiers (tous scans confondus)"""
        from django.db.models import Sum
        result = FileItem.objects.filter(file_list__device=obj).aggregate(
            total=Count('id'),
            size=Sum('size_bytes')
        )
        count = result['total'] or 0
        size_gb = (result['size'] or 0) / (1024**3)
        return format_html('{}<br><small>{:.2f} Go</small>', count, size_gb)
    files_count.short_description = "Fichiers"
    
    def storage_summary(self, obj):
        """Résumé du stockage"""
        last_scan = obj.file_lists.filter(status='completed').first()
        if not last_scan:
            return "Aucun scan disponible"
        
        total = last_scan.files.count()
        images = last_scan.files.filter(file_type='image').count()
        videos = last_scan.files.filter(file_type='video').count()
        audio = last_scan.files.filter(file_type='audio').count()
        documents = last_scan.files.filter(file_type='document').count()
        apks = last_scan.files.filter(file_type='apk').count()
        
        total_size = last_scan.files.aggregate(total=Sum('size_bytes'))['total'] or 0
        total_size_gb = total_size / (1024**3) if total_size else 0
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>📊 Dernier scan:</strong> {}<br><br>'
            '📁 Total: {} fichiers<br>'
            '🖼️ Images: {}<br>'
            '🎬 Vidéos: {}<br>'
            '🎵 Audio: {}<br>'
            '📄 Documents: {}<br>'
            '📱 APK: {}<br><br>'
            '💾 Taille totale: {:.2f} Go'
            '</div>',
            last_scan.created_at.strftime('%d/%m/%Y %H:%M'),
            total, images, videos, audio, documents, apks,
            total_size_gb
        )
    storage_summary.short_description = "Résumé stockage"
    
    def view_files_link(self, obj):
        """Lien direct vers tous les fichiers de l'appareil"""
        url = reverse('admin:api_fileitem_changelist') + f'?file_list__device__id__exact={obj.id}'
        return format_html(
            '<a class="button" href="{}" style="background: #28a745; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none;">📁 Voir tous les fichiers</a>',
            url
        )
    view_files_link.short_description = "Actions"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            file_lists_count=Count('file_lists', distinct=True)
        )
        return queryset
    
    # Actions
    def activate_devices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ {updated} appareil(s) activé(s).")
    activate_devices.short_description = "✅ Activer la sélection"
    
    def deactivate_devices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"❌ {updated} appareil(s) désactivé(s).")
    deactivate_devices.short_description = "❌ Désactiver la sélection"
    
    def mark_as_emulator(self, request, queryset):
        updated = queryset.update(is_emulator=True)
        self.message_user(request, f"🖥️ {updated} appareil(s) marqué(s) comme émulateur.")
    mark_as_emulator.short_description = "🖥️ Marquer comme émulateur"
    
    def request_file_list_action(self, request, queryset):
        count = 0
        for device in queryset:
            if device.is_active:
                # Logique d'envoi de commande à implémenter
                count += 1
        self.message_user(request, f"📱 Demande envoyée à {count} appareil(s).")
    request_file_list_action.short_description = "📱 Demander la liste des fichiers"


@admin.register(FileList)
class FileListAdmin(admin.ModelAdmin):
    """Administration des scans - Version complète"""
    
    list_display = [
        'id',
        'scan_id_short',
        'device_info',
        'status_colored',
        'file_count',
        'total_size_display',
        'created_at_short',
        'view_files_link'
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
        'device__model'
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
    actions = ['download_as_json']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('device').prefetch_related('files')
    
    def scan_id_short(self, obj):
        return obj.scan_id[:20] + '...' if len(obj.scan_id) > 20 else obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def device_info(self, obj):
        return format_html(
            '{} {}<br><small>{}</small>',
            obj.device.manufacturer,
            obj.device.model,
            obj.device.android_id[:8] + '...'
        )
    device_info.short_description = "Appareil"
    
    def status_colored(self, obj):
        colors = {
            'pending': '#ffc107',
            'scanning': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Statut"
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = "Fichiers"
    
    def total_size_display(self, obj):
        size = obj.total_size_bytes
        if size < 1024**3:
            return f"{size/1024**2:.1f} Mo"
        return f"{size/1024**3:.2f} Go"
    total_size_display.short_description = "Taille totale"
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_short.short_description = "Créé le"
    
    def files_preview(self, obj):
        stats = obj.files.values('file_type').annotate(count=Count('id'))
        
        html = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
        icons = {
            'image': '🖼️', 'video': '🎬', 'audio': '🎵',
            'document': '📄', 'apk': '📱', 'archive': '🗜️',
        }
        
        for stat in stats:
            icon = icons.get(stat['file_type'], '📁')
            html += f'<div style="background: #e9ecef; padding: 5px 10px; border-radius: 3px;">{icon} {stat["file_type"]}: {stat["count"]}</div>'
        
        html += '</div>'
        return format_html(html)
    files_preview.short_description = "Aperçu"
    
    def stats_summary(self, obj):
        try:
            stats = FileScanStats.objects.get(file_list=obj)
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '🖼️ Images: {} ({} Mo)<br>'
                '🎬 Vidéos: {} ({} Mo)<br>'
                '🎵 Audio: {} ({} Mo)<br>'
                '📄 Documents: {} ({} Mo)<br>'
                '📱 APK: {} ({} Mo)<br>'
                '👁️ Cachés: {}'
                '</div>',
                stats.images_count, stats.images_size / 1024**2,
                stats.videos_count, stats.videos_size / 1024**2,
                stats.audio_count, stats.audio_size / 1024**2,
                stats.documents_count, stats.documents_size / 1024**2,
                stats.apks_count, stats.apks_size / 1024**2,
                stats.hidden_files_count
            )
        except FileScanStats.DoesNotExist:
            return "Statistiques non disponibles"
    stats_summary.short_description = "Détails"
    
    def view_files_link(self, obj):
        url = reverse('admin:api_fileitem_changelist') + f'?file_list__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">🔍 Voir fichiers</a>', url)
    view_files_link.short_description = "Actions"
    
    def download_as_json(self, request, queryset):
        count = queryset.count()
        self.message_user(request, f"📥 Export de {count} scan(s) demandé.")
    download_as_json.short_description = "📥 Exporter en JSON"


@admin.register(FileItem)
class FileItemAdmin(admin.ModelAdmin):
    """Administration des fichiers individuels"""
    
    list_display = [
        'name_truncated',
        'file_type_icon',
        'extension',
        'size_formatted',
        'device_model',
        'scan_date_short',
        'path_preview'
    ]
    
    list_filter = [
        'file_type',
        'extension',
        'is_hidden',
        'file_list__device__manufacturer'
    ]
    
    search_fields = [
        'name',
        'path',
        'file_list__device__android_id',
        'file_list__device__model'
    ]
    
    readonly_fields = [field.name for field in FileItem._meta.fields]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('file_list__device')
    
    def name_truncated(self, obj):
        return obj.name[:40] + '...' if len(obj.name) > 40 else obj.name
    name_truncated.short_description = "Nom"
    
    def file_type_icon(self, obj):
        icons = {
            'image': '🖼️', 'video': '🎬', 'audio': '🎵',
            'document': '📄', 'apk': '📱', 'archive': '🗜️',
        }
        return icons.get(obj.file_type, '📁')
    file_type_icon.short_description = " "
    
    def size_formatted(self, obj):
        if obj.size_bytes < 1024:
            return f"{obj.size_bytes} o"
        elif obj.size_bytes < 1024**2:
            return f"{obj.size_bytes/1024:.1f} Ko"
        elif obj.size_bytes < 1024**3:
            return f"{obj.size_bytes/1024**2:.1f} Mo"
        return f"{obj.size_bytes/1024**3:.2f} Go"
    size_formatted.short_description = "Taille"
    
    def device_model(self, obj):
        return f"{obj.file_list.device.manufacturer} {obj.file_list.device.model}"
    device_model.short_description = "Appareil"
    
    def scan_date_short(self, obj):
        return obj.file_list.created_at.strftime('%d/%m/%Y')
    scan_date_short.short_description = "Date scan"
    
    def path_preview(self, obj):
        return obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
    path_preview.short_description = "Chemin"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FileScanStats)
class FileScanStatsAdmin(admin.ModelAdmin):
    """Administration des statistiques"""
    
    list_display = [
        'id',
        'scan_device',
        'images_count',
        'videos_count',
        'audio_count',
        'documents_count',
        'apks_count',
        'total_size_display'
    ]
    
    list_filter = ['created_at']
    readonly_fields = [field.name for field in FileScanStats._meta.fields]
    
    def scan_device(self, obj):
        return str(obj.file_list.device)
    scan_device.short_description = "Appareil"
    
    def total_size_display(self, obj):
        total = (obj.images_size + obj.videos_size + obj.audio_size + 
                obj.documents_size + obj.apks_size)
        return f"{total/1024**3:.2f} Go"
    total_size_display.short_description = "Total"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False