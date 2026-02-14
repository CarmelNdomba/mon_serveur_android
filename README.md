openapi: 3.0.3
info:
  title: Android Device Management API
  version: "2.0"
  description: API pour l'enregistrement des appareils Android
paths:
  /api/devices/register/:
    post:
      summary: Enregistrer un appareil Android
      description: >
        Endpoint public pour l'enregistrement initial d'un appareil. Le téléphone envoie ses infos
        et reçoit une `server_key` pour les futures communications.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - androidId
              properties:
                androidId:
                  type: string
                  description: Identifiant unique de l'appareil
                model:
                  type: string
                manufacturer:
                  type: string
                android_version:
                  type: string
                brand:
                  type: string
                hardware:
                  type: string
                soc_manufacturer:
                  type: string
                soc_model:
                  type: string
                supported_abis:
                  type: string
                  description: Liste des ABIs séparées par des virgules, ex: "arm64-v8a,armeabi-v7a"
                board:
                  type: string
                product:
                  type: string
                device_code:
                  type: string
                sdk_level:
                  type: integer
                build_id:
                  type: string
                build_fingerprint:
                  type: string
                build_type:
                  type: string
                build_tags:
                  type: string
                build_time:
                  type: integer
                  description: Timestamp UNIX (secondes depuis 1970)
                security_patch:
                  type: string
                  format: date
                total_ram:
                  type: integer
                  maximum: 2147483647
                  description: RAM totale en Mo
                total_storage:
                  type: integer
                  maximum: 2147483647
                  description: Stockage total en Mo
                available_storage:
                  type: integer
                  maximum: 2147483647
                  description: Stockage disponible en Mo
                screen_width:
                  type: integer
                screen_height:
                  type: integer
                screen_density:
                  type: integer
                screen_refresh_rate:
                  type: integer
                battery_capacity:
                  type: integer
                battery_level:
                  type: integer
                  minimum: 0
                  maximum: 100
                is_charging:
                  type: boolean
                sim_operator:
                  type: string
                sim_country:
                  type: string
                sim_carrier_name:
                  type: string
                network_operator:
                  type: string
                network_country:
                  type: string
                network_type:
                  type: string
                is_roaming:
                  type: boolean
                phone_count:
                  type: integer
                is_dual_sim:
                  type: boolean
                language:
                  type: string
                country:
                  type: string
                timezone:
                  type: string
                is_24hour_format:
                  type: boolean
                is_rooted_score:
                  type: number
                  format: float
                is_debuggable:
                  type: boolean
                is_emulator:
                  type: boolean
                has_verified_boot:
                  type: boolean
                encryption_state:
                  type: string
                  enum: [encrypted, unencrypted, unknown]
                has_camera:
                  type: boolean
                has_nfc:
                  type: boolean
                has_bluetooth:
                  type: boolean
                has_fingerprint:
                  type: boolean
                has_face_unlock:
                  type: boolean
                has_ir_blaster:
                  type: boolean
                has_compass:
                  type: boolean
                has_gyroscope:
                  type: boolean
                has_accelerometer:
                  type: boolean
                camera_count:
                  type: integer
                camera_resolutions:
                  type: string
                  description: Liste des résolutions séparées par des virgules, ex: "12MP,64MP,12MP"
                app_version:
                  type: string
                app_build_number:
                  type: integer
                is_first_install:
                  type: boolean
                install_time:
                  type: integer
                  description: Timestamp UNIX installation initiale
                update_time:
                  type: integer
                  description: Timestamp UNIX dernière mise à jour
      responses:
        '201':
          description: Appareil enregistré avec succès
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: registered
                  message:
                    type: string
                  device_id:
                    type: integer
                  server_key:
                    type: string
                  instructions:
                    type: string
        '200':
          description: Appareil existant mis à jour
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: updated
                  message:
                    type: string
                  device_id:
                    type: integer
                  server_key:
                    type: string
                  instructions:
                    type: string
        '400':
          description: Requête invalide
        '500':
          description: Erreur serveur
