#!/usr/bin/env python3
"""Compile the real AIDL verify helper with fake HAL/authz endpoints."""
from pathlib import Path
import subprocess
import re
import sys
import tempfile
vold = Path(sys.argv[1])
tree = Path(__file__).resolve().parents[2]
assert not list((tree/'.github/vold-support').rglob('Android.bp')), 'Support templates must not declare duplicate Soong modules'
assert (vold/'nx733j/gatekeeper/Android.bp').is_file()
assert not (vold/'nx733j/gatekeeper/Android.bp.in').exists()
s = (vold/'nx733j/GatekeeperAidl.cpp').read_text()
header = (vold/'nx733j/GatekeeperAidl.h').read_text()
assert '#include <aidl/' not in header and '#include <log/' not in header
build = (vold/'Android.bp').read_text().split('name: "libvold",', 1)[1].split('cc_binary {', 1)[0]
assert '"nx733j/GatekeeperAidl.cpp"' in build
whole = re.search(r'whole_static_libs:\s*\[(.*?)\]', build, re.S).group(1)
shared = re.search(r'shared_libs:\s*\[(.*?)\]', build, re.S).group(1)
assert '"android.hardware.gatekeeper-V1-ndk_platform"' in whole
assert '"android.hardware.gatekeeper-V1-ndk_platform"' not in shared
helper = s.split('// BEGIN NX733J AIDL verification')[1].split('// END NX733J AIDL verification')[0]
decrypt = (vold/'Decrypt.cpp').read_text()
assert 'AServiceManager_isDeclared("android.hardware.gatekeeper.IGatekeeper/default")' in decrypt
assert 'VerifyGatekeeperAidl(fakeUid(user_id), handle, credential)' in decrypt
assert '::android::hardware::gatekeeper::V1_0::IGatekeeper::getService()' in decrypt
harness = '#include "' + (vold/'nx733j/GatekeeperAidl.h').resolve().as_posix() + '"\n' + r"""
#include <cassert>
#include <cstdint>
#include <cstring>
#include <memory>
#include <vector>
namespace chrome_header_probe {
constexpr int LOG_INFO = 0;
constexpr int LOG_WARNING = 1;
static_assert(LOG_INFO == 0 && LOG_WARNING == 1);
}
#define ALOGE(...) ((void)0)
struct Status { bool ok; bool isOk() const { return ok; } };
struct Token { std::vector<uint8_t> mac; int64_t userId=567, challenge=0; };
static bool gk_available, authz_available, transport_ok, authz_ok;
static int code, mac_size, verifies, forwards;
namespace ndk { struct SpAIBinder { int id; explicit SpAIBinder(int x):id(x) {} }; }
int AServiceManager_checkService(const char* name) {
    if (!strcmp(name,"android.hardware.gatekeeper.IGatekeeper/default")) return gk_available ? 1 : 0;
    assert(!strcmp(name,"android.security.authorization")); return authz_available ? 2 : 0;
}
namespace aidl { namespace android { namespace hardware { namespace gatekeeper {
struct GatekeeperVerifyResponse { int statusCode, timeoutMs; Token hardwareAuthToken; };
struct IGatekeeper {
    static constexpr int STATUS_OK=0, STATUS_REENROLL=1;
    static std::shared_ptr<IGatekeeper> fromBinder(ndk::SpAIBinder b) {
        return b.id ? std::make_shared<IGatekeeper>() : nullptr;
    }
    Status verify(int32_t uid, int64_t challenge, const std::vector<uint8_t>& handle,
                  const std::vector<uint8_t>& credential, GatekeeperVerifyResponse* response) {
        ++verifies; assert(uid==100000 && challenge==0);
        assert(handle == std::vector<uint8_t>({1,2}) && credential == std::vector<uint8_t>({3,4}));
        response->statusCode=code; response->timeoutMs=30000;
        response->hardwareAuthToken.mac.assign(mac_size, 42);
        return {transport_ok};
    }
};
}} namespace security { namespace authorization {
struct IKeystoreAuthorization {
    static std::shared_ptr<IKeystoreAuthorization> fromBinder(ndk::SpAIBinder b) {
        return b.id ? std::make_shared<IKeystoreAuthorization>() : nullptr;
    }
    Status addAuthToken(const Token& token) {
        ++forwards; assert(token.mac==std::vector<uint8_t>(32,42));
        assert(token.userId==567 && token.challenge==0); return {authz_ok};
    }
};
}}}}
""" + helper + r"""
int main() {
    for (int scenario=0; scenario<9; ++scenario) {
        gk_available=authz_available=transport_ok=authz_ok=true;
        code=0; mac_size=32; verifies=forwards=0;
        switch(scenario) {
        case 1: code=1; break;
        case 2: code=-1; break;
        case 3: code=-2; break;
        case 4: gk_available=false; break;
        case 5: transport_ok=false; break;
        case 6: mac_size=31; break;
        case 7: authz_available=false; break;
        case 8: authz_ok=false; break;
        }
        assert(VerifyGatekeeperAidl(100000,{1,2},{3,4}) == (scenario<2));
        assert(forwards == ((scenario<2 || scenario==8) ? 1 : 0));
        assert(verifies == (scenario==4 ? 0 : 1));
    }
    verifies=forwards=0;
    assert(!VerifyGatekeeperAidl(100000,{}, {3,4}));
    assert(!VerifyGatekeeperAidl(100000,{1,2}, {}));
    assert(verifies==0 && forwards==0);
}
"""
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    (p/'test.cpp').write_text(harness)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(p/'test.cpp'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=10)
print('Gatekeeper AIDL: success, reenroll, rejection, timeout, absent services, transport/token/authz failures and empty input passed')
