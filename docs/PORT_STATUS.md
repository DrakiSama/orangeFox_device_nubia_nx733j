# Port NX733J: procedencia y validación

Este port conserva OrangeFox `fox_12.1`, el producto `ofrp_NX733J` y su interfaz.
La evidencia de hardware de TWRP no equivale a una prueba física de este OrangeFox.

## Revisiones revisadas

| Componente | Revisión |
|---|---|
| TWRP device tree, `twrp-16.0` | `ef8821868512e8a60b9c1b1f4c7b0fd797dce186` |
| OrangeFox device tree, `main` inicial | `8ca75f4e2b9afc0451187aea1ffb8719c6378040` |
| OrangeFox al retomar el trabajo | `53b8ecb`, más BoardConfig y dos parches sin commit |
| OrangeFox recovery, `fox_12.1` | `857e3fed0bcd86b6fa90ac6b951cceaa2c3c7e96` |
| OrangeFox vendor, `fox_12.1` | `fbe4d49c96acace3802c53c12cad0a62903c381f` |
| Sincronizador oficial | `17938bf8a0a328d2bc42cfd2f538417df10db169` |

Los HEAD de los tres repositorios principales se contrastaron con sus ramas remotas.
Se revisó el historial reciente TWRP, incluyendo batería/ADSP, haptics, CPU tardía,
diagnóstico, límites IMG, flasheo lógico y resultados CLI.
`file-audit.csv` clasifica la comparación completa de archivos, incluidos blobs,
contra el commit funcional `9493361` y la corrección final de un acento en `device.mk`
(excluye estos nuevos informes).

## Trabajo recuperado y completado

- Se preservaron los commits anteriores de particiones, kernel/DTBO, integridad binaria e inicialización.
- Se verificaron las siete particiones lógicas EROFS, grupo `qti_dynamic_partitions`, super de
  17179869184 bytes y recovery dedicada de 104857600 bytes. No se inventó `odm_dlkm`.
- Se finalizaron los servicios HAL: boot, Gatekeeper, KeyMint, qseecomd, ssgtzd y touch.
  El init anterior iniciaba `vendor.boot-qti` sin que existiera ese nombre de servicio.
- El fstab de firmware dejó de fijar `modem_a`; usa `slotselect` y montaje de lectura.
- Se recuperó el helper vendor_dlkm moderno: mapper existente, slot válido, EROFS,
  fallback ext4 de lectura sin replay del journal. Corre en segundo plano para no retrasar CPU/UI.
- Los helpers de batería, CPU y diagnóstico se instalan en `/sbin`; no quedan ocultos por `/vendor`.
  ADSP no se reinicia si está funcionando y no se cambia su firmware, NV ni políticas de carga.
- Se restauraron vibración directa Awinic y `/tmp/nx733j-cpu-temp`; no se activa el HAL de vibración.
- Se conservaron los blobs de crypto, FBE v2 y metadata. No se degradó crypto para ocultar errores.
- Se movieron `FOX_*` a `vendorsetup.sh`. `FOX_VERSION` produce un error explícito en esta base;
  se sustituyó por `FOX_MAINTAINER_PATCH_VERSION=1`.
- Se desactivó `OF_SUPPORT_ALL_BLOCK_OTA_UPDATES`: el source lo declara incompatible con VANILLA.
  Esto no elimina Virtual A/B; conserva la integración vanilla del dispositivo.
- Se adaptó la inclusión Virtual A/B a `compression.mk` de Android 12.1 y se conservó
  `ro.virtual_ab.compression.xor.enabled=true`, el contenido adicional del include moderno.
  Esa propiedad no incorpora soporte XOR a las bibliotecas antiguas; las OTA con snapshots
  modernos siguen requiriendo validación y no se anuncian como compatibles.
- Se corrigió el idioma a `TW_DEFAULT_LANGUAGE=es-ES`, que existe en los recursos OrangeFox.
- `vendor/recovery/config/common.mk` no existe en el vendor oficial revisado. El sync oficial
  conserva `vendor/twrp/config/common.mk` y añade hooks OrangeFox a build/make, Soong y vendor/recovery.
  Por eso se usa ese common.mk, manteniendo el producto y el recovery OrangeFox.
- Se retiró `com.android.crashrecovery:service-crashrecovery`: es un jar de system_server de Android
  moderno, ajeno al runtime recovery y ausente en la base Android 12. No es una dependencia FBE.
- Se conservaron las configuraciones existentes de pantalla, timezone y herramientas cuando no
  había evidencia suficiente para sustituirlas. `TW_LOAD_PREBUILT_MODULES_AT_FIRST` es heredado;
  fox_12.1 usa su orden nativo de módulos y no consume ese flag. No se declara una prioridad validada.

## Estado de los siete parches

| Parche TWRP | Resolución OrangeFox |
|---|---|
| `twrp-flags-columns.patch` | Portado semánticamente. Las columnas ya eran correctas; se endureció el parser contra comentarios, líneas malformadas/largas y duplicados, preservando etiquetas con espacios. |
| `image-size-preflight.patch` | Portado. Se reemplazó la ejecución de `simg2img` que descartaba el resultado por libsparse, con validación expandida previa a escritura/discard y comprobación de write/fsync/close. |
| `logical-image-flash.patch` | Portado con las APIs C++17 de esta base y enlace explícito a libdm. Mantiene lock OTA, estados/snapshots, mapper/slot, target linear en super, capacidad, readonly, unmount, identidad y escritura sin create/truncate/discard. |
| `nx733j-haptics.patch` | Portado a `minuitwrp/events.cpp`, con duration_aw/activate_aw. |
| `image-target-message.patch` | Portado al catálogo inglés y a `extra-languages/languages/es-ES.xml`. |
| `late-cpu-sensor.patch` | Portado al DataManager OrangeFox; la ausencia inicial del enlace no desactiva permanentemente las lecturas. |
| `cli-result.patch` | Portado conservando getval, console_message/warning/error, xset y postprocesado OrangeFox. Distingue resultado real de las señales de navegación GUI/OTA. |

Se agregó `nx733j-super-protection.patch`: OrangeFox crea `/super` automáticamente y lo marcaba
flasheable. Ahora no aparece como destino IMG normal; su función de backup existente se conserva.
La lista ordenada completa está en `.github/patches/series`.

## Pruebas

`python3 tools/validate-port.py /ruta/bootable/recovery` ejecuta:

| Suite | Cobertura |
|---|---|
| CLI | 36 escenarios FIFO, errores locales, dispatcher real, getval/consola OrangeFox, sideload y completion/action GUI |
| CPU discovery | 5 escenarios con sysfs y reloj simulados, incluyendo sensor tardío, PMIC incorrecto y error al crear enlace |
| CPU tardía | 3 combinaciones de flags compiladas, sensor inicialmente ausente y posterior lectura |
| Preflight sparse | 11 escenarios con discard y sin discard, incluidos fsync y close fallidos |
| IMG lógico | 47 escenarios de OTA, mapping, capacidad, apertura y escritura con E/S simulada |
| Parser flags | Código real compilado: comentarios, columnas, espacios, líneas inválidas/largas, duplicados y EOF; protección super |
| Árbol del dispositivo | Particiones, FBE, destinos protegidos, referencias init, XML, sintaxis shell y slots |
| Validadores de artefactos | Ramdisk sintético, symlinks absolutos internos, shell ausente, extracción CPIO, archivo malformado y tamaño excesivo; no sustituye la imagen real |

Los cinco tests TWRP se conservaron y adaptaron a APIs/nombres/rutas reales OrangeFox.
El timeout externo del test CPU subió a 30 s para soportar carga concurrente en WSL;
las aserciones del reloj simulado siguen exigiendo exactamente 29 esperas como máximo.
Los tests compilan funciones extraídas del source real; no compilan todo Android ni prueban drivers.
El resultado ejecutado se registra en `validation-results.txt`.

## Build y artefactos

El workflow manual usa exclusivamente una VM GitHub-hosted ubuntu-22.04, como TWRP,
con 16 GiB de swap y cuatro trabajos. No usa WSL ni runner local. Usa el sincronizador oficial,
revisiones recovery/vendor fijadas, device tree del commit exacto, ccache, tests previos,
registro del manifiesto resuelto y diffs de los proyectos parcheados.
Publica artifacts y logs, nunca releases automáticas. No limpia SDKs ni swap de un self-hosted.

`build-validated.sh` exige un árbol preparado y un destino device vacío; no resetea trabajo ajeno.
Valida el máximo de 100 MiB, el staging y el ramdisk extraído de la imagen final, incluidos
intérpretes mediante resolución de symlinks dentro del ramdisk. Genera SHA256SUMS solamente
si existe una imagen que supera esas comprobaciones.

Consultar `validation-results.txt` para el estado real del intento local de build. Hasta que exista
una imagen validada, su tamaño y SHA-256 se consideran **no disponibles**.

## Corrección del contrato de API de recovery

El primer build de GitHub Actions confirmó el error de `config.mk:741` guardado en
`build-lunch.log`: System SDK 32 frente a PRODUCT_SHIPPING_API_LEVEL 35. El mensaje
posterior de repositorio/producto ausente era una consecuencia del fallo de dumpvars.

La revisión del source mostró que ese contrato corresponde al producto Android completo.
En SDK 32, este producto de recovery deja PRODUCT_SHIPPING_API_LEVEL y BOARD_SHIPPING_API_LEVEL
sin declarar para las propiedades intermedias de sistema/vendor. BoardConfig añade exclusivamente
al prop.default de recovery `ro.product.first_api_level=35` y `ro.board.first_api_level=35`
mediante TARGET_RECOVERY_ADDITIONAL_PROPERTIES y una extensión acotada de la receta recovery. El validador
ahora exige ambos valores 35 en el ramdisk final y rechaza ausencias o valores contradictorios.
Para plataformas distintas de SDK 32, se mantiene la declaración PRODUCT_SHIPPING_API_LEVEL=35.
No se modifica System SDK, crypto, FBE, particiones ni el firmware del teléfono.

Esto corrige la integración del producto recovery; no incorpora nuevas APIs ni garantiza
que los blobs modernos funcionen sobre esta base. La conclusión anterior de que este error
por sí solo obligaba a migrar de plataforma era demasiado amplia. La compilación remota
siguiente debe validar la corrección y mostrar cualquier incompatibilidad adicional.
Los tests evalúan el fragmento Make real en SDK 32, 35 y 36, y prueban el rechazo de una
propiedad de lanzamiento incorrecta en un ramdisk sintético.

Referencias del source revisado: `build/make/core/config.mk:716-742`,
`build/make/core/main.mk:290-306`, `build/make/core/sysprop.mk:325-359` y
`build/make/core/Makefile:2195-2209`. Los resultados anteriores en validation-results.txt
son históricos; no certifican este nuevo commit. Toda nueva compilación usa GitHub Actions.

## Compatibilidad de system_dlkm en el build

El build de Actions `35533627202` superó la comprobación de API y encontró el siguiente
límite de Android 12.1: la lista permitida de particiones dinámicas en config.mk no incluye
`system_dlkm`. El nuevo parche `.github/build-patches/system-dlkm-name.patch` añade únicamente
ese nombre; conserva la validación de nombres y todas las particiones/tamaños del dispositivo.
Se aplica antes de lunch y su diff queda registrado entre los artefactos de fuentes del build.

El aplicador exige uno de dos SHA-256 exactos revisados: config.mk de TeamWin o ese mismo
archivo con el hook oficial OrangeFox_A12.sh añadido por sync. Prueba su fragmento Make real:
antes rechaza el mapa NX733J, después acepta sus siete particiones y sigue rechazando nombres
inválidos. CI usa TeamWin/android_build `1b692e2248609f50a27c48cce53b7445cecdcfc5`.
Esto permite declarar el mapa stock para `recoveryimage`; no implementa un generador de
system_dlkm.img ni autoriza fabricar o flashear super. El código genérico de releasetools
itera los nombres del grupo, pero no se valida aquí la construcción de una ROM completa.

## Enlace de libdm en Android 12.1

Actions `35535105449` superó lunch y Soong, pero Ninja buscó un libdm.so inexistente.
`system/core/fs_mgr/libdm/Android.bp` declara libdm como cc_library_static, con
libext2_uuid en static_libs. El parche de flasheo lógico ahora enlaza ambas estáticamente;
libsparse permanece compartida. No se eliminó libdm ni se alteraron los controles del writer.
La confirmación de enlace final corresponde al siguiente build remoto, no a los tests simulados.

## Macro de quick backup y caché

Actions `35535735469` alcanzó la compilación de recovery y falló en twrp-functions.cpp:
el valor OF_QUICK_BACKUP_LIST tenía comillas en BoardConfig y orangefox.mk lo envolvía
otra vez, produciendo una macro C++ inválida. Se conserva la misma lista sin comillas
adicionales en Make. Los demás valores entre comillas usan reglas diferentes y no se
modificaron indiscriminadamente. La caché del compilador ahora se guarda también tras
un build fallido, con claves únicas por intento, para reutilizar objetos ya compilados.

## Validación GRF y propiedades exclusivas de recovery

Actions `35540480808` compiló el código hasta el empaquetado, pero post_process_props rechazó
ro.board.first_api_level=35 dentro de vendor/build.prop SDK 32. La separación anterior sólo
cubría el contrato de producto y era incompleta. Ahora ambas propiedades reales de lanzamiento
se añaden en la receta que construye exclusivamente recovery/prop.default, después de las
propiedades intermedias validadas; no se altera ni desactiva post_process_props.
El parche de Makefile admite únicamente hashes revisados del source base y del sync oficial.

La prueba usa el post_process_props.py real para verificar que el vendor incompatible sigue
siendo rechazado, y ejecuta la receta Make para comprobar que las propiedades 35 aparecen en
recovery sin falsear ro.vendor.build.version.sdk. El verificador final sigue exigiendo ambos
valores 35 en el ramdisk extraído de la imagen. No se genera ni publica una imagen vendor.

## Límites y riesgos conocidos

- FBE con PIN, batería y haptics tienen evidencia del TWRP de referencia, no de este nuevo OrangeFox.
- Android 12 como base de recovery y Android 15/16 como firmware del teléfono son capas distintas.
  APIs KeyMint/FBE y blobs SDK35 deben probarse sobre el firmware instalado. No se garantiza descifrado
  por mantener flags o por pasar pruebas simuladas; no se migró automáticamente a fox_14.1/16.
- El writer lógico falla si no puede demostrar estado OTA idle, snapshots vacíos, mapa linear directo
  y capacidad suficiente. Un estado ausente, desconocido, readonly o mapper distinto se rechaza;
  no se "repara" metadata OTA ni se cancela una actualización para habilitar flasheo.
- Escribir una partición lógica es irreversible y una interrupción puede dejarla incompleta;
  estos controles no son una transacción ni hacen una imagen compatible con AVB/firmware.
- Los módulos se obtienen de vendor/vendor_dlkm/vendor_boot stock: los nombres configurados no
  demuestran su disponibilidad o compatibilidad con el kernel cargado.
- El README anterior declaraba ADB, MTP, display, touch, fastbootd, FBE y backup funcionales;
  se conserva esa procedencia como antecedente, sin atribuirla al build nuevo. OTG requiere especial
  revisión porque TWRP documenta una posible identificación errónea de UFS como almacenamiento USB.
- WiFi se conserva como configuración heredada; no se anuncia como funcional.

## Primera prueba física

1. Guardar fuera del teléfono la recovery anterior funcional y los backups propios. Verificar
   producto NX733J/PQ84A01, slot actual y tamaño de recovery antes de planificar una escritura.
   No asumir que `fastboot boot` funciona con esta imagen dedicada sin kernel.
2. Usar exclusivamente una imagen de este port con build, tamaño, SHA-256 y ramdisk verificados.
   No probar IMG lógicas como primer paso de validación.
3. Tras entrar a recovery, comprobar display, brillo, touch sin lag, vibración y navegación.
4. Ejecutar `adb shell sh /sbin/nx733j-diagnose.sh` y guardar su salida; verificar slot, batería,
   ADSP en running y cpuss-0-0. `stopped` en un helper oneshot puede indicar fin normal, no fallo.
5. Probar el PIN en la UI y comprobar acceso a un archivo de prueba conocido. No guardar ni compartir
   PIN o datos personales en logs; registrar únicamente éxito/fallo y versión de firmware.
6. Comprobar ADB/MTP, lectura de archivos de prueba, montajes EROFS y `/metadata`. Verificar módulos
   reales mediante `/proc/modules`; probar OTG sólo tras distinguir almacenamiento externo de UFS.
7. Verificar que super, modem, persist, frp y vbmeta no aparecen como destinos IMG permitidos.
   Comparar el mensaje de destino de imágenes con el slot seleccionado antes de cualquier escritura.
8. Probar un comando CLI de lectura, como `adb shell twrp get tw_cpu_temp`, y su código de salida.
   Un ZIP fallido/exit code se valida más adelante con un paquete de prueba controlado, no con firmware.
9. Comprobar entrada/salida de fastbootd y reinicio al sistema sin cambiar de slot ni tocar AVB/NV.
10. Sólo después de validar lo anterior, planificar backup/restore y pruebas IMG raw/sparse separadas,
    con backups verificados y sin OTA pendiente. Nunca crear o cancelar snapshots para forzar la prueba.

## Fuentes de integración

- [Build oficial OrangeFox](https://wiki.orangefox.tech/dev/building)
- [Sincronizador oficial](https://gitlab.com/OrangeFox/sync)
- [Variables OrangeFox](https://wiki.orangefox.tech/dev/build_vars)
- [TWRP NX733J](https://github.com/DrakiSama/twrp_device_nubia_nx733j/tree/twrp-16.0)
