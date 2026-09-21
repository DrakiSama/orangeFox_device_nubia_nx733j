# Gatekeeper AIDL client for recovery

Frozen AIDL v1 definitions copied unchanged from AOSP android-14.0.0_r1:
https://android.googlesource.com/platform/hardware/interfaces/+/android-14.0.0_r1/gatekeeper/aidl/aidl_api/android.hardware.gatekeeper/1/

Use KeyMint v1 HardwareAuthToken, already present in the pinned Android 12.1 base.
The helper only verifies the supplied credential and forwards the returned HAT to
KeystoreAuthorization. It never enrolls, deletes users or changes credentials.
Select AIDL only when declared in VINTF; preserve the existing HIDL path otherwise.
Failures and retry timeouts must stop the attempt without forwarding a token.
