# Primera versión funcional: revisión del 23/09/2026

Imagen de referencia: e7ec3e09fa8fcaa8940e66ea42af7e1949e6852e.
Build: https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35683505355
Pruebas: https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35683505411
Ambas ejecuciones terminaron correctamente; el build incluye verificación del ramdisk.

## Comprobado en el dispositivo

- OrangeFox operativo por ADB; el usuario confirma interfaz, PIN y batería.
- `twrp.user.0.decrypt=1`; `/data/media/0/Android` accesible y /data montado en F2FS.
- Batería sysfs 34 %, `tw_battery=34`, estado Charging y `charging_now=1`.
- `tw_cpu_temp=51` en la consulta; lectura puntual, no una prueba térmica.
- Gatekeeper, KeyMint, Keystore2 y BootControl HIDL activos al revisar.
- USB `mtp,adb` y almacenamiento anunciado por MTP; transferencia MTP no probada.
- Slot activo b; system, system_ext, product, vendor, odm, vendor_dlkm y system_dlkm
  montados uno a uno con EROFS ro en un directorio temporal y desmontados después.

## Limitaciones observadas

- Usuario 999: `twrp.user.999.decrypt=0`. El propietario identifica este perfil
  con aplicaciones clonadas. No afecta al desbloqueo del usuario 0, pero los datos
  de esas apps no quedan validados para backup o recuperación.
- `ssgtzd` no enlaza por libssl.so ausente; el descifrado principal funciona pese a ello.
- Keystore2 abortó inicialmente al no encontrar KeyMint; posteriormente estaba activo
  y el descifrado tuvo éxito. Queda pendiente endurecer el orden de arranque.
- Avisos de montaje de las siete particiones en recovery.log: los montajes manuales
  de solo lectura pasan, pero no se certifica el montaje desde todos los flujos GUI.
- Falta un recurso visual Progress/indeterminate033 y aparece un aviso de terminal;
  no se declara validada la terminal integrada.
- Hay dispositivos mapper con sufijo -cow. No se alteraron snapshots ni se probó flasheo.
- Backup/restauración, OTA, escritura de particiones, fastbootd, OTG, WiFi y vibración
  no se probaron en esta revisión. No equivale a soporte completo de todas las funciones.

La revisión no flasheó ni borró particiones, claves o datos. Los registros completos
se conservan localmente; no se publican identificadores ni contenido personal.
