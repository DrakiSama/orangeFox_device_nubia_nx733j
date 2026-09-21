# Primera prueba física: detenido en splash

Diagnóstico ADB solicitado por el propietario, 2026-09-21 (hora del log del dispositivo).
El build de Actions 35546442876, commit e2eebfa, terminó correctamente y publicó artefactos.
El usuario indicó haber instalado su imagen. El teléfono informa OrangeFox R12.0_1 y SDK 32;
no se verificó byte a byte la partición instalada contra el artefacto.

## Hallazgo principal

El proceso recovery sigue vivo, esperando en futex. Su log confirma inicialización DRM,
commit gráfico exitoso y carga del paquete splash. La UI completa todavía no se carga.
El hilo principal registra repetidamente que espera
`android.system.keystore2.IKeystoreService/default`. El servicio keystore2 se reinicia.
Por tanto, la evidencia apunta a una espera de servicios de descifrado después del splash;
no demuestra un fallo del panel ni permite dar el touch por validado.

## Fallos observados

- keystore2: `Unrecognized manifest.version 8.0 (libvintf@4.0)` en
  `/vendor/etc/vintf/manifest/boot-service.qti.xml`.
- KeyMint: falta el símbolo `_ZN7android7IBinder8withLockERKNSt3__18functionIFvvEEE`,
  requerido por `/vendor/lib64/libbinder_ndk-sdk35.so`. Es incompatibilidad de ABI;
  agregar un nombre de biblioteca o un enlace simbólico no aporta ese símbolo.
- Boot HAL: falta `android.hardware.boot-V1-ndk.so`.
- ssgtzd: falta `libssl.so`, requerida por libnicm_utils.so.
- qseecomd: inicia y abre /dev/smcinvoke, pero falla al iniciar listeners y se reinicia.
  La causa interna de ese fallo todavía no está determinada.

No se eliminó crypto ni se probaron PINs. No se reinició recovery ni el teléfono, ni se
flashearon particiones, cambiaron slots o escribieron datos mediante los comandos del diagnóstico.
Los montajes existentes los había realizado recovery; /metadata estaba montada rw por recovery.
Los logs completos se guardaron localmente en device-diagnostics, fuera del repositorio, y no
se publican porque pueden incluir identificadores y rutas propias del dispositivo.

## Hardware que sí respondió

ADB disponible; DRM inicializado a 1216 x 2688 y splash cargado. ADSP identificado por nombre
`3000000.remoteproc-adsp` estaba running. El enlace CPU apuntaba a un sensor cpuss-0-0 y
reportó 45900; batería reportó 67%. El helper oneshot terminado no se considera un fallo.
Gatekeeper estaba running. Esto no certifica descifrado, haptics ni navegación táctil.

## Próximo trabajo necesario

Preparar un conjunto compatible de runtime Binder, libvintf, KeyMint y sus dependencias,
sobre una base OrangeFox adecuada o mediante backports explícitos revisados. El runtime de
Android 12.1 actual no satisface los blobs SDK35 copiados. También se debe limitar la espera
infinita de keystore para poder mostrar un error útil, sin anunciar descifrado funcional.
No basta con cambiar la versión del XML, omitir las validaciones o copiar libbinder de stock:
son contratos de ABI y servicios que deben integrarse y probarse conjuntamente.
No se lanzó otro build, porque el diagnóstico no aporta todavía una solución de runtime validada.
