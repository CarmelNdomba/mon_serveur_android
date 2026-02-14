# api/models.py
from django.db import models
import secrets
import hashlib

class Device(models.Model):
    """
    Modèle complet pour stocker toutes les informations d'un téléphone
    Tous les champs sont optionnels sauf android_id, model, manufacturer
    """
    
    # ===== IDENTIFIANTS =====
    android_id = models.CharField(max_length=100, unique=True, verbose_name="ID Android")
    device_key = models.CharField(max_length=64, unique=True, blank=True, verbose_name="Clé d'authentification")
    
    # ===== INFOS DE BASE (obligatoires) =====
    model = models.CharField(max_length=100, verbose_name="Modèle")
    manufacturer = models.CharField(max_length=100, verbose_name="Fabricant")
    android_version = models.CharField(max_length=20, default="Inconnue", verbose_name="Version Android")
    
    # ===== 1. INFOS MATÉRIELLES =====
    brand = models.CharField(max_length=100, blank=True, verbose_name="Marque")
    hardware = models.CharField(max_length=100, blank=True, verbose_name="Plateforme matérielle")
    soc_manufacturer = models.CharField(max_length=100, blank=True, verbose_name="Fabricant SoC")
    soc_model = models.CharField(max_length=100, blank=True, verbose_name="Modèle SoC")
    supported_abis = models.CharField(max_length=200, blank=True, verbose_name="Architectures CPU")
    board = models.CharField(max_length=100, blank=True, verbose_name="Carte mère")
    product = models.CharField(max_length=100, blank=True, verbose_name="Produit")
    device_code = models.CharField(max_length=100, blank=True, verbose_name="Nom de code")
    
    # ===== 2. INFOS SYSTÈME =====
    sdk_level = models.IntegerField(null=True, blank=True, verbose_name="Niveau API")
    build_id = models.CharField(max_length=100, blank=True, verbose_name="ID de compilation")
    build_fingerprint = models.CharField(max_length=255, blank=True, verbose_name="Empreinte build")
    build_type = models.CharField(max_length=20, blank=True, verbose_name="Type de build")
    build_tags = models.CharField(max_length=100, blank=True, verbose_name="Tags de build")
    build_time = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de compilation")
    security_patch = models.CharField(max_length=20, blank=True, verbose_name="Patch de sécurité")
    
    # ===== 3. MÉMOIRE ET STOCKAGE =====
    total_ram = models.IntegerField(null=True, blank=True, verbose_name="RAM totale (MB)")
    total_storage = models.IntegerField(null=True, blank=True, verbose_name="Stockage total (MB)")
    available_storage = models.IntegerField(null=True, blank=True, verbose_name="Stockage disponible (MB)")
    
    # ===== 4. ÉCRAN =====
    screen_width = models.IntegerField(null=True, blank=True, verbose_name="Largeur écran")
    screen_height = models.IntegerField(null=True, blank=True, verbose_name="Hauteur écran")
    screen_density = models.IntegerField(null=True, blank=True, verbose_name="Densité écran")
    screen_refresh_rate = models.IntegerField(null=True, blank=True, verbose_name="Taux de rafraîchissement")
    
    # ===== 5. BATTERIE =====
    battery_capacity = models.IntegerField(null=True, blank=True, verbose_name="Capacité batterie (mAh)")
    battery_level = models.IntegerField(null=True, blank=True, verbose_name="Niveau batterie (%)")
    is_charging = models.BooleanField(default=False, verbose_name="En charge")
    
    # ===== 6. RÉSEAU ET TÉLÉPHONIE =====
    sim_operator = models.CharField(max_length=50, blank=True, verbose_name="Opérateur SIM")
    sim_country = models.CharField(max_length=10, blank=True, verbose_name="Pays SIM")
    sim_carrier_name = models.CharField(max_length=100, blank=True, verbose_name="Nom opérateur")
    network_operator = models.CharField(max_length=50, blank=True, verbose_name="Opérateur réseau")
    network_country = models.CharField(max_length=10, blank=True, verbose_name="Pays réseau")
    network_type = models.CharField(max_length=20, blank=True, verbose_name="Type de réseau")
    is_roaming = models.BooleanField(default=False, verbose_name="En roaming")
    phone_count = models.IntegerField(null=True, blank=True, verbose_name="Nombre de SIM")
    is_dual_sim = models.BooleanField(default=False, verbose_name="Dual SIM")
    
    # ===== 7. LOCALISATION =====
    language = models.CharField(max_length=10, blank=True, verbose_name="Langue")
    country = models.CharField(max_length=10, blank=True, verbose_name="Pays")
    timezone = models.CharField(max_length=50, blank=True, verbose_name="Fuseau horaire")
    is_24hour_format = models.BooleanField(default=False, verbose_name="Format 24h")
    
    # ===== 8. SÉCURITÉ =====
    is_rooted_score = models.FloatField(default=0.0, verbose_name="Score de root")
    is_debuggable = models.BooleanField(default=False, verbose_name="Mode debug")
    is_emulator = models.BooleanField(default=False, verbose_name="Émulateur")
    has_verified_boot = models.BooleanField(default=False, verbose_name="Boot vérifié")
    encryption_state = models.CharField(max_length=50, blank=True, verbose_name="État chiffrement")
    
    # ===== 9. CAPTEURS ET FONCTIONNALITÉS =====
    has_camera = models.BooleanField(default=False, verbose_name="Caméra")
    has_nfc = models.BooleanField(default=False, verbose_name="NFC")
    has_bluetooth = models.BooleanField(default=False, verbose_name="Bluetooth")
    has_fingerprint = models.BooleanField(default=False, verbose_name="Empreinte")
    has_face_unlock = models.BooleanField(default=False, verbose_name="Reconnaissance faciale")
    has_ir_blaster = models.BooleanField(default=False, verbose_name="IR Blaster")
    has_compass = models.BooleanField(default=False, verbose_name="Boussole")
    has_gyroscope = models.BooleanField(default=False, verbose_name="Gyroscope")
    has_accelerometer = models.BooleanField(default=False, verbose_name="Accéléromètre")
    camera_count = models.IntegerField(default=0, verbose_name="Nombre de caméras")
    camera_resolutions = models.CharField(max_length=255, blank=True, verbose_name="Résolutions caméra")
    
    # ===== 10. INFOS APPLICATION =====
    app_version = models.CharField(max_length=20, blank=True, verbose_name="Version app")
    app_build_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro de build")
    is_first_install = models.BooleanField(default=False, verbose_name="Première installation")
    install_time = models.BigIntegerField(null=True, blank=True, verbose_name="Date installation")
    update_time = models.BigIntegerField(null=True, blank=True, verbose_name="Date mise à jour")
    
    # ===== MÉTADONNÉES =====
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Dernière connexion")
    
    def generate_key(self):
        """Génère une clé unique pour le device"""
        unique_string = f"{self.android_id}{secrets.token_hex(16)}"
        return hashlib.sha256(unique_string.encode()).hexdigest()
    
    def save(self, *args, **kwargs):
        if not self.device_key:
            self.device_key = self.generate_key()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.manufacturer} {self.model} ({self.android_version})"
    
    class Meta:
        verbose_name = "Appareil"
        verbose_name_plural = "Appareils"
        ordering = ['-created_at']


# ===== NOUVEAUX MODÈLES POUR LA GESTION DES FICHIERS =====

class FileList(models.Model):
    """
    Modèle pour stocker la liste des métadonnées de fichiers d'un appareil
    Un "scan" ou "instantané" du système de fichiers à un moment T
    """
    
    # Types de statut pour le scan
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('scanning', 'Scan en cours'),
        ('completed', 'Terminé'),
        ('partial', 'Partiel'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    # Relation avec l'appareil
    device = models.ForeignKey(
        Device, 
        on_delete=models.CASCADE, 
        related_name='file_lists',
        verbose_name="Appareil"
    )
    
    # Identifiant unique du scan
    scan_id = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="ID du scan",
        help_text="Identifiant unique généré par le téléphone pour ce scan"
    )
    
    # Métadonnées de la collecte
    scan_requested_at = models.DateTimeField(
        verbose_name="Demandé le",
        help_text="Moment où la commande a été envoyée"
    )
    scan_started_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Début du scan",
        help_text="Moment où le téléphone a commencé le scan"
    )
    scan_completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Fin du scan",
        help_text="Moment où le téléphone a terminé le scan"
    )
    scan_duration_ms = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Durée (ms)",
        help_text="Durée totale du scan en millisecondes"
    )
    
    # Statistiques du scan
    total_files = models.IntegerField(
        default=0, 
        verbose_name="Total fichiers",
        help_text="Nombre total de fichiers trouvés"
    )
    total_size_bytes = models.BigIntegerField(
        default=0, 
        verbose_name="Taille totale (octets)",
        help_text="Taille cumulée de tous les fichiers en octets"
    )
    
    # Commande associée (pour traçabilité)
    command_id = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="ID commande",
        help_text="Identifiant de la commande qui a déclenché ce scan"
    )
    
    # Statut du scan
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Statut"
    )
    
    # Message d'erreur si échec
    error_message = models.TextField(
        blank=True, 
        verbose_name="Message d'erreur",
        help_text="Description de l'erreur si le scan a échoué"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Créé le"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Mis à jour le"
    )
    
    class Meta:
        verbose_name = "Liste de fichiers"
        verbose_name_plural = "Listes de fichiers"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['scan_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Scan {self.scan_id} - {self.device} - {self.total_files} fichiers"
    
    @classmethod
    def cleanup_old_scans(cls, device, keep_last=5):
        """
        Nettoie les vieux scans pour un appareil
        Garde seulement les N derniers scans
        """
        old_scans = cls.objects.filter(device=device).order_by('-created_at')[keep_last:]
        count = old_scans.count()
        old_scans.delete()
        return count


class FileItem(models.Model):
    """
    Modèle pour stocker les métadonnées d'un fichier individuel
    """
    
    # Types de fichiers
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('apk', 'Application APK'),
        ('archive', 'Archive'),
        ('database', 'Base de données'),
        ('log', 'Fichier log'),
        ('temporary', 'Fichier temporaire'),
        ('system', 'Fichier système'),
        ('other', 'Autre'),
    ]
    
    # Relation avec la liste parente
    file_list = models.ForeignKey(
        FileList, 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name="Liste parente"
    )
    
    # ===== INFORMATIONS DE BASE =====
    
    # Chemin et nom (stockés séparément pour les recherches)
    path = models.TextField(
        verbose_name="Chemin complet",
        help_text="Chemin absolu du fichier (ex: /storage/emulated/0/DCIM/photo.jpg)"
    )
    parent_path = models.TextField(
        blank=True,
        verbose_name="Dossier parent",
        help_text="Dossier contenant le fichier (ex: /storage/emulated/0/DCIM/)"
    )
    name = models.CharField(
        max_length=512, 
        verbose_name="Nom du fichier",
        help_text="Nom du fichier avec extension"
    )
    extension = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Extension",
        help_text="Extension du fichier (jpg, mp3, pdf, etc.)"
    )
    
    # ===== MÉTADONNÉES DU FICHIER =====
    
    size_bytes = models.BigIntegerField(
        verbose_name="Taille (octets)",
        help_text="Taille du fichier en octets"
    )
    
    # Dates (stockées en timestamp pour faciliter les comparaisons)
    last_modified = models.BigIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Dernière modification (timestamp)",
        help_text="Timestamp de la dernière modification"
    )
    last_accessed = models.BigIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Dernier accès (timestamp)",
        help_text="Timestamp du dernier accès"
    )
    created_at_time = models.BigIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Date création (timestamp)",
        help_text="Timestamp de création du fichier"
    )
    
    # ===== CLASSIFICATION =====
    
    file_type = models.CharField(
        max_length=20, 
        choices=FILE_TYPE_CHOICES, 
        default='other',
        verbose_name="Type de fichier"
    )
    mime_type = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Type MIME",
        help_text="Type MIME détecté (image/jpeg, video/mp4, etc.)"
    )
    
    # ===== PERMISSIONS =====
    
    is_readable = models.BooleanField(
        default=True, 
        verbose_name="Lisible",
        help_text="Le fichier est-il accessible en lecture ?"
    )
    is_writable = models.BooleanField(
        default=False, 
        verbose_name="Inscriptible",
        help_text="Le fichier est-il accessible en écriture ?"
    )
    is_hidden = models.BooleanField(
        default=False, 
        verbose_name="Caché",
        help_text="Le fichier est-il caché (commence par un point) ?"
    )
    is_directory = models.BooleanField(
        default=False, 
        verbose_name="Est un dossier",
        help_text="S'agit-il d'un dossier plutôt que d'un fichier ?"
    )
    
    # ===== INTÉGRITÉ (optionnel) =====
    
    md5_hash = models.CharField(
        max_length=32, 
        blank=True, 
        verbose_name="MD5",
        help_text="Empreinte MD5 du fichier (si calculée)"
    )
    sha1_hash = models.CharField(
        max_length=40, 
        blank=True, 
        verbose_name="SHA1",
        help_text="Empreinte SHA1 du fichier (si calculée)"
    )
    
    # ===== MÉTADONNÉES SPÉCIFIQUES AUX MÉDIAS =====
    
    # Pour les images/vidéos
    media_width = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Largeur",
        help_text="Largeur en pixels (pour images/vidéos)"
    )
    media_height = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Hauteur",
        help_text="Hauteur en pixels (pour images/vidéos)"
    )
    media_duration_ms = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Durée (ms)",
        help_text="Durée en millisecondes (pour audio/vidéo)"
    )
    
    # Pour les photos (EXIF)
    media_date_taken = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Date de prise de vue",
        help_text="Timestamp EXIF de la photo"
    )
    media_gps_lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Latitude GPS",
        help_text="Coordonnées GPS de la photo (si disponibles)"
    )
    media_gps_lng = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Longitude GPS",
        help_text="Coordonnées GPS de la photo (si disponibles)"
    )
    
    # ===== POUR LES APPLICATIONS (APK) =====
    
    apk_package_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom du package",
        help_text="Nom du package Android (pour les APK)"
    )
    apk_version_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Code de version",
        help_text="Version code de l'application"
    )
    apk_version_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom de version",
        help_text="Nom de version de l'application"
    )
    apk_min_sdk = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SDK minimum",
        help_text="Niveau API minimum requis"
    )
    
    # ===== MÉTADONNÉES =====
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Créé le"
    )
    
    class Meta:
        verbose_name = "Fichier"
        verbose_name_plural = "Fichiers"
        indexes = [
            # Index pour recherche rapide par type
            models.Index(fields=['file_list', 'file_type']),
            models.Index(fields=['file_list', 'file_type', 'size_bytes']),
            
            # Index pour recherche par nom
            models.Index(fields=['name']),
            models.Index(fields=['extension']),
            
            # Index pour recherche par chemin
            models.Index(fields=['parent_path']),
            models.Index(fields=['path']),
            
            # Index pour recherche par date
            models.Index(fields=['last_modified']),
            
            # Index pour les fichiers cachés
            models.Index(fields=['is_hidden']),
        ]
        ordering = ['path']
    
    def __str__(self):
        size_mb = self.size_bytes / (1024 * 1024)
        return f"{self.path} ({size_mb:.2f} MB)"
    
    def save(self, *args, **kwargs):
        """
        Surcharge de save pour auto-remplir certains champs
        """
        # Auto-détection de l'extension
        if not self.extension and '.' in self.name:
            self.extension = self.name.split('.')[-1].lower()
        
        # Auto-détection du dossier parent
        if not self.parent_path and '/' in self.path:
            self.parent_path = '/'.join(self.path.split('/')[:-1]) + '/'
        
        # Auto-détection du type de fichier basé sur l'extension
        if self.file_type == 'other' and self.extension:
            extension_to_type = {
                # Images
                'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image',
                'bmp': 'image', 'webp': 'image', 'heic': 'image',
                # Vidéos
                'mp4': 'video', 'avi': 'video', 'mkv': 'video', 'mov': 'video',
                'wmv': 'video', 'flv': 'video', '3gp': 'video',
                # Audio
                'mp3': 'audio', 'wav': 'audio', 'aac': 'audio', 'ogg': 'audio',
                'flac': 'audio', 'm4a': 'audio',
                # Documents
                'pdf': 'document', 'doc': 'document', 'docx': 'document',
                'xls': 'document', 'xlsx': 'document', 'ppt': 'document',
                'pptx': 'document', 'txt': 'document', 'rtf': 'document',
                'odt': 'document', 'ods': 'document',
                # Archives
                'zip': 'archive', 'rar': 'archive', '7z': 'archive',
                'tar': 'archive', 'gz': 'archive',
                # Applications
                'apk': 'apk',
                # Bases de données
                'db': 'database', 'sqlite': 'database',
                # Logs
                'log': 'log',
                # Temporaires
                'tmp': 'temporary', 'temp': 'temporary', 'cache': 'temporary',
            }
            self.file_type = extension_to_type.get(self.extension, 'other')
        
        super().save(*args, **kwargs)


class FileScanStats(models.Model):
    """
    Modèle optionnel pour les statistiques agrégées des scans
    Évite de recalculer les stats à chaque requête
    """
    file_list = models.OneToOneField(
        FileList, 
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name="Liste de fichiers"
    )
    
    # Statistiques par type
    images_count = models.IntegerField(default=0)
    images_size = models.BigIntegerField(default=0)
    videos_count = models.IntegerField(default=0)
    videos_size = models.BigIntegerField(default=0)
    audio_count = models.IntegerField(default=0)
    audio_size = models.BigIntegerField(default=0)
    documents_count = models.IntegerField(default=0)
    documents_size = models.BigIntegerField(default=0)
    apks_count = models.IntegerField(default=0)
    apks_size = models.BigIntegerField(default=0)
    archives_count = models.IntegerField(default=0)
    archives_size = models.BigIntegerField(default=0)
    
    # Statistiques par dossier important
    dcim_count = models.IntegerField(default=0, help_text="Photos/Vidéos dans DCIM")
    dcim_size = models.BigIntegerField(default=0)
    downloads_count = models.IntegerField(default=0, help_text="Fichiers dans Download")
    downloads_size = models.BigIntegerField(default=0)
    whatsapp_count = models.IntegerField(default=0, help_text="Fichiers WhatsApp")
    whatsapp_size = models.BigIntegerField(default=0)
    
    # Top 10 plus gros fichiers (stocké en JSON pour éviter une requête supplémentaire)
    largest_files = models.JSONField(default=list, help_text="Top 10 des plus gros fichiers")
    
    # Statistiques de fichiers cachés
    hidden_files_count = models.IntegerField(default=0)
    hidden_files_size = models.BigIntegerField(default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Statistiques de scan"
        verbose_name_plural = "Statistiques de scans"
    
    def __str__(self):
        return f"Stats pour {self.file_list.scan_id}"
    
    @classmethod
    def generate_from_file_list(cls, file_list):
        """
        Génère les statistiques à partir d'une FileList
        """
        from django.db.models import Sum, Count, Q
        
        files = file_list.files
        
        stats = cls(file_list=file_list)
        
        # Stats par type
        for file_type in ['image', 'video', 'audio', 'document', 'apk', 'archive']:
            queryset = files.filter(file_type=file_type)
            count = queryset.count()
            size = queryset.aggregate(total=Sum('size_bytes'))['total'] or 0
            
            setattr(stats, f'{file_type}s_count', count)
            setattr(stats, f'{file_type}s_size', size)
        
        # Stats par dossier
        dcim_files = files.filter(path__icontains='/DCIM/')
        stats.dcim_count = dcim_files.count()
        stats.dcim_size = dcim_files.aggregate(total=Sum('size_bytes'))['total'] or 0
        
        downloads_files = files.filter(path__icontains='/Download/')
        stats.downloads_count = downloads_files.count()
        stats.downloads_size = downloads_files.aggregate(total=Sum('size_bytes'))['total'] or 0
        
        whatsapp_files = files.filter(Q(path__icontains='/WhatsApp/') | Q(path__icontains='/WhatsApp Business/'))
        stats.whatsapp_count = whatsapp_files.count()
        stats.whatsapp_size = whatsapp_files.aggregate(total=Sum('size_bytes'))['total'] or 0
        
        # Fichiers cachés
        hidden_files = files.filter(is_hidden=True)
        stats.hidden_files_count = hidden_files.count()
        stats.hidden_files_size = hidden_files.aggregate(total=Sum('size_bytes'))['total'] or 0
        
        # Top 10 plus gros fichiers
        largest = files.order_by('-size_bytes')[:10].values('name', 'path', 'size_bytes', 'file_type')
        stats.largest_files = list(largest)
        
        stats.save()
        return stats