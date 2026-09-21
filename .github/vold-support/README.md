# Gatekeeper AIDL client for recovery

Frozen AIDL v1 definitions copied unchanged from AOSP android-14.0.0_r1:
https://android.googlesource.com/platform/hardware/interfaces/+/android-14.0.0_r1/gatekeeper/aidl/aidl_api/android.hardware.gatekeeper/1/

Use KeyMint v1 HardwareAuthToken, already present in the pinned Android 12.1 base.
The helper only verifies the supplied credential and forwards the returned HAT to
KeystoreAuthorization. It never enrolls, deletes users or changes credentials.
Select AIDL only when declared in VINTF; preserve the existing HIDL path otherwise.
Failures and retry timeouts must stop the attempt without forwarding a token.

Android.bp.in is deliberately inactive in the device tree. The patch installer
renames it to Android.bp only in system/vold/nx733j/gatekeeper, so Soong sees one
Gatekeeper interface module instead of scanning both the template and its copy.

GatekeeperAidl.cpp owns the Binder and logging dependencies. Its public header
contains only the verification declaration and standard types, keeping syslog
macros out of Decrypt.cpp and its libchrome logging headers.
