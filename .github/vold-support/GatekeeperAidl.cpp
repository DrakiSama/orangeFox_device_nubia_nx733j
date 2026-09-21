// SPDX-License-Identifier: Apache-2.0
#include "GatekeeperAidl.h"
#include <aidl/android/hardware/gatekeeper/IGatekeeper.h>
#include <aidl/android/security/authorization/IKeystoreAuthorization.h>
#include <android/binder_manager.h>
#include <vector>
#include <cstdint>
#include <log/log.h>

// BEGIN NX733J AIDL verification
bool VerifyGatekeeperAidl(uint32_t uid, const std::vector<uint8_t>& handle,
                                 const std::vector<uint8_t>& credential) {
    using aidl::android::hardware::gatekeeper::IGatekeeper;
    using aidl::android::hardware::gatekeeper::GatekeeperVerifyResponse;
    using aidl::android::security::authorization::IKeystoreAuthorization;
    if (handle.empty() || credential.empty()) return false;
    auto service = IGatekeeper::fromBinder(::ndk::SpAIBinder(AServiceManager_checkService(
        "android.hardware.gatekeeper.IGatekeeper/default")));
    if (!service) {
        ALOGE("Gatekeeper AIDL service is unavailable");
        return false;
    }
    GatekeeperVerifyResponse response;
    auto result = service->verify(static_cast<int32_t>(uid), 0, handle, credential, &response);
    if (!result.isOk()) {
        ALOGE("Gatekeeper AIDL transaction failed");
        return false;
    }
    if (response.statusCode != IGatekeeper::STATUS_OK &&
        response.statusCode != IGatekeeper::STATUS_REENROLL) {
        ALOGE("Gatekeeper AIDL rejected verification (status %d, timeout %d ms)",
              response.statusCode, response.timeoutMs);
        return false;
    }
    if (response.hardwareAuthToken.mac.size() != 32) {
        ALOGE("Gatekeeper AIDL returned an invalid authentication token");
        return false;
    }
    auto authorization = IKeystoreAuthorization::fromBinder(::ndk::SpAIBinder(
        AServiceManager_checkService("android.security.authorization")));
    if (!authorization) {
        ALOGE("Keystore authorization service is unavailable");
        return false;
    }
    // AIDL already supplies the structured HAT. Do not reinterpret or byte-swap it.
    if (!authorization->addAuthToken(response.hardwareAuthToken).isOk()) {
        ALOGE("Keystore authorization rejected the authentication token");
        return false;
    }
    return true;
}
// END NX733J AIDL verification
