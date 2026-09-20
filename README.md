# OrangeFox para Nubia Z70 Ultra — NX733J / PQ84A01

Port de los fixes del device tree TWRP `twrp-16.0` sobre **OrangeFox fox_12.1**.
Producto: `ofrp_NX733J`. Rama de desarrollo: `port/twrp-16-sync`.

## Estado real

- 🟡 Particiones EROFS, FBE v2, batería/ADSP, haptics Awinic, CPU tardía y diagnóstico integrados.
- ✅ Pruebas de código y runtime simulado: consultar [resultados](docs/validation-results.txt).
- ❌ Build bloqueado en `lunch`: System SDK 32 de fox_12.1 frente a API de lanzamiento 35 del dispositivo. No hay imagen final validada.
- 🟡 Validación física de este port: pendiente en NX733J.
- ⚠️ Flasheo IMG lógico: experimental, limitado a asignaciones existentes y sin OTA/snapshots activos.
- ❌ WiFi no validado. No se anuncia compatibilidad de OTG hasta descartar identificación errónea de UFS.

El README anterior declaraba ADB, MTP, pantalla, touch, fastbootd, FBE y backup funcionales.
Ese antecedente se conserva; no acredita esos estados en esta revisión. Los resultados de hardware
TWRP tampoco se convierten automáticamente en resultados OrangeFox.

[Informe completo, revisiones, inventario y checklist de prueba física](docs/PORT_STATUS.md).

## Pruebas sin teléfono

En Linux con Python 3, Git, Bash y g++:

```bash
git clone --branch port/twrp-16-sync https://github.com/DrakiSama/orangeFox_device_nubia_nx733j device-tree
git clone --branch fox_12.1 https://gitlab.com/OrangeFox/bootable/Recovery.git recovery-source
git -C recovery-source checkout "$(cat device-tree/.github/recovery-revision)"
python3 device-tree/tools/apply-recovery-patches.py recovery-source
python3 device-tree/tools/validate-port.py recovery-source
```

La rama debe estar publicada para clonar estos cambios; mientras sean locales, utilizar este checkout.
El aplicador rechaza revisiones no revisadas o archivos modificados y comprueba la serie completa antes de aplicarla.

## Build OrangeFox

Usar el [sincronizador oficial](https://gitlab.com/OrangeFox/sync), según la
[guía de OrangeFox](https://wiki.orangefox.tech/dev/building), como usuario normal en Linux.
No usar la antigua URL `OrangeFox/platform_manifest`.

```bash
git clone https://gitlab.com/OrangeFox/sync.git OrangeFox-sync
git -C OrangeFox-sync checkout "$(cat device-tree/.github/sync-revision)"
(cd OrangeFox-sync && bash orangefox_sync.sh --branch 12.1 --path "$HOME/fox-nx733j-build")
# Fijar las dos fuentes OrangeFox antes de aplicar los parches:
git -C "$HOME/fox-nx733j-build/bootable/recovery" fetch origin "$(cat device-tree/.github/recovery-revision)"
git -C "$HOME/fox-nx733j-build/bootable/recovery" checkout --detach FETCH_HEAD
git -C "$HOME/fox-nx733j-build/vendor/recovery" fetch origin "$(cat device-tree/.github/vendor-revision)"
git -C "$HOME/fox-nx733j-build/vendor/recovery" checkout --detach FETCH_HEAD
# Ejecutar con la ruta absoluta del device tree que contiene estos commits:
(cd "$HOME/fox-nx733j-build" && bash /ruta/absoluta/device-tree/tools/build-validated.sh /ruta/absoluta/artifacts)
```

El helper exporta el commit exacto a `device/nubia/NX733J`, aplica parches, ejecuta tests,
exporta `vendorsetup.sh`, hace `lunch ofrp_NX733J-eng` y `m recoveryimage`.
Exige un destino device vacío para no sobrescribir trabajo existente.

El common.mk correcto de esta distribución es `vendor/twrp/config/common.mk`, acompañado por
los hooks oficiales OrangeFox de build/make y vendor/recovery; el producto continúa siendo OrangeFox.

CI incluye tests automáticos y un build manual self-hosted o GitHub-hosted. Produce artifacts/logs,
con límite de recovery de **104857600 bytes**, revisión exacta, SHA-256 y verificación del ramdisk
final. No crea releases ni flashea el teléfono.

## Particiones y primera prueba

Siete particiones lógicas: system, system_ext, product, vendor, odm, vendor_dlkm y system_dlkm.
No existe odm_dlkm. `super` no se permite como destino IMG normal. Firmware modem se monta en
lectura por slot; modem no es modemst/fsg ni el almacenamiento NV.

No se incluyen instrucciones de flasheo indiscriminado: seguir el
[checklist físico](docs/PORT_STATUS.md#primera-prueba-física) después de obtener una imagen verificada.
No asumir que `fastboot boot` es compatible con esta recovery dedicada sin kernel.
