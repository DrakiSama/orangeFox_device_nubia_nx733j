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

## Corrección de la espera y salida a system

Se sustituyó AServiceManager_waitForService en el constructor de Keymaster por hasta
40 comprobaciones no bloqueantes de registro, separadas por 250 ms. Si no aparece el
servicio, el constructor conserva securityLevel vacío y los callers de KeyStorage
rechazan la operación. No se crean claves alternativas, se formatea data ni se desactiva FBE.
Se permiten reintentos posteriores; la ausencia inicial no queda almacenada permanentemente.
Las llamadas Binder posteriores a un servicio ya registrado no tienen un timeout nuevo.

Esto corrige la espera infinita observada, pero no resuelve ni acredita todavía la
compatibilidad de los blobs SDK35 con Binder/libvintf de Android 12.1. El arranque completo
y el descifrado requieren validación física de un nuevo build y trabajo de runtime adicional.
El parche se aplica al source vold fijado y se registra su diff en los artefactos del build.

El propietario solicitó volver a system al terminar el diagnóstico. El primer reboot
volvió a recovery porque BCB conservaba boot-recovery. Se respaldaron localmente 2048 bytes
del mensaje y se pusieron a cero sólo los primeros 32 bytes (campo command), verificando
que los otros 2016 no cambiaron, antes de repetir reboot system. No se cambiaron slots.


## 2026-09-21: physical crypto diagnosis and RAM validation

The bounded-keystore build reaches the menu. The remaining blockers were
verified over ADB with the user's phone running that build:

* SDK-35 libbinder_ndk requires six C++ Binder symbols absent from SDK 32.
  KeyMint and its interface libraries only import NDK APIs exported by SDK 32.
  Aliasing the SDK-35 soname to the platform NDK library in RAM allowed KeyMint
  to register. The permanent alias is scoped to audited crypto services;
  health uses a newer death-recipient API and must not use this alias.
* libvintf supports manifest schema 4.0; supplied schemas 8.0/9.0 prevented
  service discovery. Normalizing only the schema version preserves HAL versions.
  The device fragment under system was also invalid: system is framework-owned.
  Remove that duplicate; vendor fragments already declare these services.
* After these changes, KeyMint shared-secret negotiation succeeded and
  Keystore 2.0 registered successfully. No PIN was provided to the agent.
* Installed system reports Android 16, system patch 2026-02-01, vendor patch
  2025-12-01. Runtime recovery reported Android 15 and patches 2099-12-31.
  Reading the installed properties from separate read-only EROFS mounts and
  configuring them before KeyMint allowed retrieval of the metadata key.
  The generated userdata mapping mounted successfully read-only in a separate
  temporary directory. No personal files were inspected.
* Recovery then waits for HIDL BootControl 1.0/1.1. The stock AIDL service alone
  cannot satisfy the Android 12.1 client; generic HIDL service lacks its backend.
  Generic AOSP boot_control is unsuitable: its misc slot metadata CRC/magic is
  not present on this Qualcomm device. Add the official Qualcomm HIDL adapter
  linked to the existing libboot_control_qti.so; preserve the Qualcomm backend.

The startup wrapper obtains properties dynamically from the active slot, waits
at most 30 seconds for logical devices, mounts only read-only, validates values,
and fails closed rather than configuring KeyMint with fabricated versions.
The HIDL adapter still requires the full Actions build and physical validation.
Metadata-key recovery is confirmed; PIN-protected CE decryption is not yet
confirmed. ssgtzd/libssl and AIDL health compatibility remain separate issues.
Raw logs and device identifiers remain local and are not committed.
