
# Create your models here.
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