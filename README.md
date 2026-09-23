# OrangeFox Recovery · Nubia Z70 Ultra

**NX733J / PQ84A01** · Base **fox_12.1** · Producto `ofrp_NX733J` · Rama `main`

[![Pruebas de regresión](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/port-tests.yml/badge.svg?branch=main)](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/port-tests.yml)
[![Compilación de recovery](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml)

Port de OrangeFox para el Nubia Z70 Ultra, basado en el device tree TWRP
`twrp-16.0`, con parches específicos del dispositivo y compilación en GitHub Actions.
Mantenido por [DrakiSama](https://github.com/DrakiSama).

**Primera versión funcional (no oficial):** arranque, interfaz, desbloqueo con PIN
del usuario principal y porcentaje de batería comprobados en el teléfono.
Imagen de referencia: [`e7ec3e0`](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35683505355).
El perfil 999 de aplicaciones clonadas sigue sin descifrarse; no impide acceder
al almacenamiento del usuario principal, pero sus datos no se consideran recuperables.

[Compilaciones y artifacts](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml)
· [Diagnóstico en el dispositivo](docs/FIRST_BOOT_DIAGNOSIS.md)
· [Detalles técnicos del port](docs/PORT_STATUS.md)

## Estado del dispositivo

Estado documentado al **23 de septiembre de 2026**. Las pruebas en RAM y las
pruebas automáticas se distinguen de la validación de una imagen instalada.

| Componente | Estado comprobado |
| --- | --- |
| Arranque e interfaz | La imagen probada el 23/09 inicia OrangeFox y llega al almacenamiento principal. |
| ADB por USB | Confirmado; utilizado para el diagnóstico físico. |
| KeyMint y Keystore2 | Servicios activos y desbloqueo del usuario principal comprobados en el teléfono. |
| Cifrado de metadatos | Volumen descifrado en `/dev/block/dm-14` en la imagen instalada. |
| Datos protegidos con PIN (FBE/CE) | Usuario 0 desbloqueado; `/data/media/0/Android` accesible. Perfil 999 pendiente. |
| BootControl Qualcomm | Servicio HIDL activo en la imagen instalada; arranque sin intervención en RAM en esta sesión. |
| Batería y temperatura | Capacidad sysfs e interfaz coinciden (34 %), carga detectada y temperatura CPU disponible. |
| Vibración | Soporte Awinic integrado; comprobación física pendiente. |
| Flasheo de imágenes lógicas | Experimental; limitado a asignaciones existentes, sin OTA ni snapshots activos. |
| WiFi, OTG, MTP, fastbootd y backup/restauración | No se anuncian como validados en esta revisión de OrangeFox. |

## Primera versión funcional

La [compilación de `e7ec3e0`](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35683505355)
y sus [pruebas de regresión](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35683505411)
terminaron correctamente, incluida la inspección del ramdisk final.
La revisión por ADB del 23/09 confirmó el usuario 0 desbloqueado,
almacenamiento interno accesible, batería/carga y lectura de temperatura.
Las siete particiones lógicas se montaron temporalmente en solo lectura.

El usuario identifica el perfil **999** como el de aplicaciones dobles
(WhatsApp, Messenger, etc.). Su descifrado queda fuera del soporte comprobado
de esta primera versión; no se oculta el fallo ni se elimina ese perfil.

Pendientes de la revisión: `ssgtzd` no inicia por una dependencia `libssl.so`
ausente; Keystore2 tuvo un fallo inicial antes de reiniciarse y permitir el
descifrado; el registro muestra avisos de montaje del sistema desde la interfaz,
aunque los montajes manuales de solo lectura funcionaron. Backup/restauración,
flasheo, OTA, MTP con transferencia, OTG y fastbootd requieren pruebas propias.
Consulta el [informe de validación](docs/FIRST_VERSION_REVIEW.md).

## Generar con GitHub Actions

Abrir **Actions → OrangeFox NX733J - GitHub hosted → Run workflow → main**.
La compilación se ejecuta en una VM `ubuntu-22.04` de GitHub, con swap, ccache y
cuatro trabajos en paralelo, como el flujo hosted de TWRP. No requiere WSL ni runner local.
Los logs y, cuando el build pasa, la imagen y SHA256SUMS se descargan desde **Artifacts**.
La API real de lanzamiento (35) se conserva y se comprueba en el ramdisk final.

## Pruebas sin teléfono

En Linux con Python 3, Git, Bash y g++:

```bash
git clone --branch main https://github.com/DrakiSama/orangeFox_device_nubia_nx733j device-tree
git clone --branch fox_12.1 https://gitlab.com/OrangeFox/bootable/Recovery.git recovery-source
git -C recovery-source checkout "$(cat device-tree/.github/recovery-revision)"
python3 device-tree/tools/apply-recovery-patches.py recovery-source
python3 device-tree/tools/validate-port.py recovery-source
```

El aplicador rechaza revisiones no revisadas o archivos modificados y comprueba la serie completa antes de aplicarla.

<details>
<summary>Reproducir la compilación manualmente en Linux (avanzado)</summary>


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

CI incluye tests automáticos y un build manual exclusivamente GitHub-hosted. Produce artifacts/logs,
con límite de recovery de **104857600 bytes**, revisión exacta, SHA-256 y verificación del ramdisk
final. No crea releases ni flashea el teléfono.

</details>

## Particiones y primera prueba

Siete particiones lógicas: system, system_ext, product, vendor, odm, vendor_dlkm y system_dlkm.
No existe odm_dlkm. `super` no se permite como destino IMG normal. Firmware modem se monta en
lectura por slot; modem no es modemst/fsg ni el almacenamiento NV.

No se incluyen instrucciones de flasheo indiscriminado: seguir el
[checklist físico](docs/PORT_STATUS.md#primera-prueba-física) después de obtener una imagen verificada.
No asumir que `fastboot boot` es compatible con esta recovery dedicada sin kernel.

## Créditos

- [OrangeFox Recovery Project](https://gitlab.com/OrangeFox): recovery y herramientas de sincronización.
- [TeamWin](https://github.com/TeamWin): base TWRP y soporte de recuperación.
- [LineageOS / Qualcomm BootControl](bootctrl/README.md): procedencia y revisión del adaptador HIDL.

Las revisiones fijadas, licencias originales y detalles de los parches se conservan
junto al código y en la [documentación del port](docs/PORT_STATUS.md).
