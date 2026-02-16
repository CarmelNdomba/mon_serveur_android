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
        return obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
    path_preview.short_description = "Chemin"


class FileListInline(admin.TabularInline):
    """Affichage des scans dans le détail d'un appareil"""
    model = FileList
    fields = ['scan_id_short', 'status', 'total_files', 'total_size_display', 'created_at']
    readonly_fields = ['scan_id_short', 'status', 'total_files', 'total_size_display', 'created_at']
    extra = 0
    max_num = 5
    can_delete = False
    ordering = ['-created_at']
    
    def scan_id_short(self, obj):
        return obj.scan_id[:20] + '...' if len(obj.scan_id) > 20 else obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def total_size_display(self, obj):
        size = obj.total_size_bytes
        if size < 1024**3:
            return f"{size/1024**2:.1f} Mo"
        return f"{size/1024**3:.2f} Go"
    total_size_display.short_description = "Taille"


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Administration des appareils - Version simplifiée"""
    list_display = [
        'android_id_short',
        'manufacturer',
        'model',
        'is_active',
        'last_seen_ago',
        'scans_count'
    ]
    list_filter = ['manufacturer', 'is_active', 'has_camera']
    search_fields = ['android_id', 'model', 'manufacturer']
    ordering = ['-last_seen']
    readonly_fields = ['device_key', 'created_at', 'last_seen']
    
    # Actions personnalisées (en strings)
    actions = ['activate_devices', 'deactivate_devices']
    
    inlines = [FileListInline]
    
    def android_id_short(self, obj):
        return obj.android_id[:10] + '...' if len(obj.android_id) > 10 else obj.android_id
    android_id_short.short_description = "Android ID"
    
    def last_seen_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.last_seen) + " ago" if obj.last_seen else "Never"
    last_seen_ago.short_description = "Last seen"
    
    def scans_count(self, obj):
        return obj.file_lists.count()
    scans_count.short_description = "Scans"
    
    def activate_devices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} device(s) activated.")
    activate_devices.short_description = "Activate selected devices"
    
    def deactivate_devices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} device(s) deactivated.")
    deactivate_devices.short_description = "Deactivate selected devices"


@admin.register(FileList)
class FileListAdmin(admin.ModelAdmin):
    """Administration des scans - Version simplifiée"""
    list_display = [
        'id',
        'scan_id_short',
        'device_name',
        'status_colored',
        'file_count',
        'created_at_short'
    ]
    list_filter = ['status', 'device__manufacturer']
    search_fields = ['scan_id', 'device__android_id']
    readonly_fields = ['scan_id', 'device', 'created_at', 'total_files', 'total_size_bytes']
    
    inlines = [FileItemInline]
    
    def scan_id_short(self, obj):
        return obj.scan_id[:20] + '...' if len(obj.scan_id) > 20 else obj.scan_id
    scan_id_short.short_description = "Scan ID"
    
    def device_name(self, obj):
        return f"{obj.device.manufacturer} {obj.device.model}"
    device_name.short_description = "Device"
    
    def status_colored(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.status)
    status_colored.short_description = "Status"
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = "Files"
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = "Created"


@admin.register(FileItem)
class FileItemAdmin(admin.ModelAdmin):
    """Administration des fichiers - Version simplifiée"""
    list_display = [
        'name_truncated',
        'file_type',
        'size_formatted',
        'device_info',
        'scan_date'
    ]
    list_filter = ['file_type', 'extension']
    search_fields = ['name', 'path']
    readonly_fields = ['name', 'path', 'size_bytes', 'file_type', 'created_at']
    
    # ✅ Plus de méthode appelée 'actions' qui cause le conflit !
    
    def name_truncated(self, obj):
        return obj.name[:40] + '...' if len(obj.name) > 40 else obj.name
    name_truncated.short_description = "Name"
    
    def size_formatted(self, obj):
        if obj.size_bytes < 1024:
            return f"{obj.size_bytes} B"
        elif obj.size_bytes < 1024**2:
            return f"{obj.size_bytes/1024:.1f} KB"
        elif obj.size_bytes < 1024**3:
            return f"{obj.size_bytes/1024**2:.1f} MB"
        return f"{obj.size_bytes/1024**3:.2f} GB"
    size_formatted.short_description = "Size"
    
    def device_info(self, obj):
        return f"{obj.file_list.device.manufacturer} {obj.file_list.device.model}"
    device_info.short_description = "Device"
    
    def scan_date(self, obj):
        return obj.file_list.created_at.strftime('%Y-%m-%d')
    scan_date.short_description = "Scan date"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FileScanStats)
class FileScanStatsAdmin(admin.ModelAdmin):
    """Administration des statistiques - Version simplifiée"""
    list_display = [
        'id',
        'scan_device',
        'images_count',
        'videos_count',
        'total_size'
    ]
    readonly_fields = [field.name for field in FileScanStats._meta.fields]
    
    def scan_device(self, obj):
        return str(obj.file_list.device)
    scan_device.short_description = "Device"
    
    def total_size(self, obj):
        total = (obj.images_size + obj.videos_size + obj.audio_size + 
                obj.documents_size + obj.apks_size)
        return f"{total/1024**3:.2f} GB"
    total_size.short_description = "Total size"