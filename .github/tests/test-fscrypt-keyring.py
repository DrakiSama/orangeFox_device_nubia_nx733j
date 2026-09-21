#!/usr/bin/env python3
"""Compile the actual keyring helper against mocked kernel key operations."""
from pathlib import Path
import subprocess
import sys
import tempfile
s = Path(sys.argv[1]).read_text()
helper = 'static bool fscryptKeyring(' + s.split('static bool fscryptKeyring(', 1)[1].split('// Add an encryption key', 1)[0]
harness = r"""
#include <cassert>
#include <cerrno>
#include <cstring>
#include <sstream>
using key_serial_t = int;
constexpr int KEY_SPEC_SESSION_KEYRING = -3;
static std::ostringstream sink;
#define PLOG(level) sink
static int existing, lookup_error, create_error, creates;
int keyctl_search(int ring, const char* type, const char* name, int dest) {
    assert(ring == KEY_SPEC_SESSION_KEYRING && dest == 0);
    assert(!strcmp(type, "keyring") && !strcmp(name, "fscrypt"));
    if (existing) return existing;
    errno = lookup_error; return -1;
}
int add_key(const char* type, const char* name, const void* payload, unsigned long size, int ring) {
    ++creates;
    assert(!strcmp(type, "keyring") && !strcmp(name, "fscrypt"));
    assert(payload == nullptr && size == 0 && ring == KEY_SPEC_SESSION_KEYRING);
    if (create_error) { errno = create_error; return -1; }
    return existing = 42;
}
""" + helper + r"""
int main() {
    int key;
    existing = 17;
    assert(fscryptKeyring(&key) && key == 17 && creates == 0);
    existing = 0; lookup_error = ENOKEY;
    assert(fscryptKeyring(&key) && key == 42 && creates == 1);
    assert(fscryptKeyring(&key) && key == 42 && creates == 1);
    existing = 0; creates = 0; lookup_error = EACCES;
    assert(!fscryptKeyring(&key) && creates == 0);
    lookup_error = ENOKEY; create_error = EDQUOT;
    assert(!fscryptKeyring(&key) && creates == 1);
}
"""
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    (p/'test.cpp').write_text(harness)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(p/'test.cpp'), '-o', str(p/'test')], check=True)
    subprocess.run([str(p/'test')], check=True, timeout=10)
print('fscrypt keyring: existing, absent, reuse, denied lookup and denied creation passed')
