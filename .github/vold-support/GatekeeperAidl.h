// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cstdint>
#include <vector>

// Keep Binder/logging headers out of Decrypt.cpp: libchrome defines LOG_INFO
// and LOG_WARNING as C++ constants, which conflict with syslog macros.
bool VerifyGatekeeperAidl(uint32_t uid, const std::vector<uint8_t>& handle,
                         const std::vector<uint8_t>& credential);
