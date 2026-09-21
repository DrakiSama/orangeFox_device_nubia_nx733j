#!/usr/bin/env python3
"""Compile the real polling helper against a virtual service and clock."""
from pathlib import Path
import subprocess
import sys
import tempfile
source = Path(sys.argv[1]).read_text()
helper = source.split('static ::ndk::SpAIBinder WaitForRecoveryKeystore() {', 1)[1].split('Keymaster::Keymaster() {', 1)[0]
helper = 'static ::ndk::SpAIBinder WaitForRecoveryKeystore() {' + helper
constructor = source.split('Keymaster::Keymaster() {', 1)[1].split('bool Keymaster::generateKey', 1)[0]
assert 'AServiceManager_waitForService' not in constructor
assert 'binder = WaitForRecoveryKeystore()' in constructor
assert 'if (!keystore2Service)' in constructor
harness = r'''#include <cassert>
#include <chrono>
#include <sstream>
struct AIBinder {};
static AIBinder service;
static int checks, sleeps, available;
static long elapsed;
static const char keystore2_service_name[] = "test-keystore";
static std::ostringstream sink;
#define LOG(level) sink
namespace ndk {
struct SpAIBinder {
    AIBinder* ptr = nullptr;
    SpAIBinder() = default;
    explicit SpAIBinder(AIBinder* value) : ptr(value) {}
};
}
namespace std { namespace this_thread {
void sleep_for(std::chrono::milliseconds duration) {
    ++sleeps; elapsed += duration.count();
}
}}
AIBinder* AServiceManager_checkService(const char*) {
    ++checks; return available && checks >= available ? &service : nullptr;
}
''' + helper + r'''
int main() {
    for (int threshold : {1, 6, 40, 0}) {
        checks = sleeps = elapsed = 0; available = threshold;
        auto result = WaitForRecoveryKeystore();
        assert(bool(result.ptr) == bool(threshold));
        assert(checks == (threshold ? threshold : 40));
        assert(sleeps == checks - 1);
        assert(elapsed <= 9750);
    }
    checks = sleeps = elapsed = 0; available = 1;
    assert(WaitForRecoveryKeystore().ptr == &service);
    assert(checks == 1 && sleeps == 0);
}
'''
with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary)
    (path/'test.cpp').write_text(harness)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(path/'test.cpp'), '-o', str(path/'test')], check=True)
    subprocess.run([str(path/'test')], check=True, timeout=10)
print('Keystore startup: immediate, late, last poll, unavailable and subsequent recovery cases passed; no infinite wait')
