# OrangeFox Recovery · Nubia Z70 Ultra

**NX733J / PQ84A01** · Base **fox_12.1** · Producto `ofrp_NX733J` · Rama `main`

[![Pruebas de regresión](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/port-tests.yml/badge.svg?branch=main)](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/port-tests.yml)
[![Compilación de recovery](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml)

Port de OrangeFox para el Nubia Z70 Ultra, basado en el device tree TWRP
`twrp-16.0`, con parches específicos del dispositivo y compilación en GitHub Actions.
Mantenido por [DrakiSama](https://github.com/DrakiSama).

**En desarrollo:** OrangeFox ya inicia y permite acceder a la interfaz.
El descifrado de metadatos funcionó en pruebas por ADB; el desbloqueo completo
con PIN todavía no está confirmado en una imagen nueva.

[Compilaciones y artifacts](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/workflows/build.yml)
· [Diagnóstico en el dispositivo](docs/FIRST_BOOT_DIAGNOSIS.md)
· [Detalles técnicos del port](docs/PORT_STATUS.md)

## Estado del dispositivo

Estado documentado al **21 de septiembre de 2026**. Las pruebas en RAM y las
pruebas automáticas se distinguen de la validación de una imagen instalada.

| Componente | Estado comprobado |
| --- | --- |
| Arranque e interfaz | El build `72b1525` inicia OrangeFox y llega al menú. |
| ADB por USB | Confirmado; utilizado para el diagnóstico físico. |
| KeyMint y Keystore2 | Arranque, registro de servicios y negociación de secretos comprobados con correcciones en RAM. |
| Cifrado de metadatos | Clave recuperada y volumen descifrado montado en solo lectura durante el diagnóstico. |
| Datos protegidos con PIN (FBE/CE) | Pendiente de validación en la nueva imagen. |
| BootControl Qualcomm | Adaptador compilado; ajuste de bibliotecas comprobado en RAM: desbloquea el montaje de `/data` y permite llegar al menú. |
| Batería, temperatura y vibración | Soporte ADSP, detección tardía de CPU y haptics Awinic integrados; validación completa pendiente. |
| Flasheo de imágenes lógicas | Experimental; limitado a asignaciones existentes, sin OTA ni snapshots activos. |
| WiFi, OTG, MTP, fastbootd y backup/restauración | No se anuncian como validados en esta revisión de OrangeFox. |

## Últimos avances

La revisión [`6a3b8e3`](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/commit/6a3b8e3)
incorpora las correcciones identificadas por ADB:

- Compatibilidad Binder NDK para los servicios de cifrado.
- Manifiestos VINTF compatibles con la base Android 12.1 y declaraciones en su ubicación correcta.
- Lectura de la versión y los parches del firmware instalado antes de iniciar KeyMint,
  mediante montajes EROFS de solo lectura y usando el slot activo.
- Adaptador HIDL BootControl sobre la biblioteca Qualcomm del dispositivo.

Las **nueve suites de regresión** de esa revisión
[pasaron en Actions](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35561296423).
La [compilación `6a3b8e3`](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35561318301)
terminó correctamente. La prueba física encontró un bloqueo de BootControl por
bibliotecas incompatibles; su corrección se comprobó en RAM y está integrada en `main`.
También se corrigió la inicialización del keyring de sesión `fscrypt`: la
validación de FBE con este último cambio requiere una nueva imagen.
El [build anterior que llega al menú](https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/actions/runs/35552798531)
corresponde a `72b1525` y todavía presenta los fallos de descifrado diagnosticados.

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
