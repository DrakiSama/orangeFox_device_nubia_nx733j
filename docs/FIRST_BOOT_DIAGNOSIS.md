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


## Follow-up: compiled 6a3b8e3, splash wait and FBE provisioning

The Actions image built successfully, but physical startup stopped at the splash.
KeyMint and Keystore2 were running and the installed OS/patch properties were
correct, confirming the preceding startup fixes in the compiled image.

The HIDL adapter was present, but boot-hal-1-2 loaded SDK-32 libc++/libbase before
opening the Qualcomm backend. Missing symbols were __libcpp_verbose_abort and
android::base::HexString. Starting that service with process-local LD_PRELOAD of
/vendor/lib64/libcxx.so and /vendor/lib64/libbase-sdk35.so registered BootControl.
Recovery then reported successful metadata decryption, mounted /data and reached
the file manager. The permanent vendor init override retains the original HIDL
interfaces and limits preloading to this service.

FBE subsequently failed after the kernel successfully installed the first key:
"Unable to find device keyring: Required key not available". The absent fscrypt
session keyring prevents adding the fscrypt-provisioning key. The fallback then
tries incompatible wrapping and reports EINVAL; that is a secondary failure.
The reviewed KeyUtil.cpp patch creates an empty fscrypt session keyring only on
ENOKEY, reuses an existing one, and preserves permission/creation failures.
It does not erase or replace stored key blobs or alter encryption flags.
Actual FBE/CE decryption with this patch still requires the next compiled image.
A compiled helper test covers existing, missing, reuse and error cases in CI.


## Follow-up: 753b2b9 init rejection and Gatekeeper AIDL

Physical boot logs showed init rejecting the vendor override of boot-hal-1-2:
"overrides another service across the treble boundary", plus duplicate HIDL
interface declarations. The original service remained active without LD_PRELOAD.
Replace the override with a patch to OrangeFox's original platform init file.
Validation now inspects that actual file and rejects duplicate boot service
entries in the unpacked image.

Starting BootControl manually with its required libraries unblocked recovery.
The compiled keyring fix worked: systemwide keys, fscrypt-provisioning keys and
user DE keys loaded, /data mounted, and OrangeFox displayed decrypt_pin.
The user entered the PIN on the device; three attempts failed before verification
because Decrypt.cpp requested HIDL Gatekeeper while the device only provides AIDL.

The new vold path selects Gatekeeper AIDL when declared by VINTF, uses frozen
AOSP v1 definitions and forwards the returned structured HardwareAuthToken to
KeystoreAuthorization. It preserves the previous HIDL path for other devices.
It does not enroll/delete users, modify credentials or log supplied credentials.
Rejection, retry timeout, missing services, malformed token and authorization
failure stop the attempt. Successful PIN/CE unlock remains unconfirmed until
this newly compiled client is tested physically.


## Battery percentage missing (2026-09-22)

On the installed image, sysfs reported capacity 52 and status Charging, while
`tw_battery` and `tw_battery_charge` were empty. Recovery logcat repeatedly waited
for the absent `android.hardware.health@2.0::IHealth/default` service.
The pinned Recovery Android.mk evaluates the legacy-battery CFLAG before its
custom battery path block sets the legacy variable, so the path alone is insufficient.
BoardConfig now explicitly enables `TW_USE_LEGACY_BATTERY_SERVICES` before that
conditional is evaluated. The existing monitor reads capacity/status every second,
including retrying when ADSP exposes sysfs after startup. This change requires a
new image; the percentage display has not yet been verified on that image.
