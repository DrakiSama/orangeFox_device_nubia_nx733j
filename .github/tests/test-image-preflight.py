#!/usr/bin/env python3
"""Exercise the actual sparse flash method with fake I/O; never opens a device."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text(encoding='utf-8')
start = source.index('bool TWPartition::Flash_Sparse_Image(')
end = source.index('\nbool TWPartition::Flash_Image_FI', start)
method = source[start:end]
prefix = r'''
#include <cassert>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <string>
struct Msg {
    template<class... T> Msg(T...) {}
    template<class... T> Msg operator()(T...) { return *this; }
};
namespace msg { constexpr int kError = 1; }
#define LOGERR(...) ((void)0)
#define gui_msg(...) ((void)0)
#define gui_err(...) ((void)0)
struct sparse_file {};
struct State {
    bool input_ok=true, import_ok=true, output_ok=true, sync_ok=true, close_ok=true;
    int64_t expanded=100;
    int write_result=0, output_opens=0, writes=0, discards=0;
    int closes=0, destroys=0;
} state;
int fake_open(const char*, int flags) {
    if (flags == O_RDONLY) return state.input_ok ? 10 : -1;
    ++state.output_opens;
    return state.output_ok ? 20 : -1;
}
int fsync(int) { return state.sync_ok ? 0 : -1; }
int fake_close(int fd) { ++state.closes; return fd == 20 && !state.close_ok ? -1 : 0; }
#define open fake_open
#define close fake_close
sparse_file object;
sparse_file* sparse_file_import(int, bool, bool) { return state.import_ok ? &object : nullptr; }
int64_t sparse_file_len(sparse_file*, bool, bool) { return state.expanded; }
void sparse_file_destroy(sparse_file*) { ++state.destroys; }
int sparse_file_write(sparse_file*, int, bool, bool, bool) { ++state.writes; return state.write_result; }
class TWPartition {
public:
    uint64_t Size=100;
    std::string Display_Name="fake", Actual_Block_Device="fake-device";
    bool Flash_Sparse_Image(const std::string&);
    void BlkDiscard() { ++state.discards; }
};
'''
suffix = r'''
int main() {
    TWPartition part;
    int cases=0;
    auto no_writes = [&]() { assert(state.output_opens==0 && state.writes==0 && state.discards==0); ++cases; };
    state=State{}; state.input_ok=false;
    assert(!part.Flash_Sparse_Image("fake.img")); no_writes();
    state=State{}; state.import_ok=false;
    assert(!part.Flash_Sparse_Image("fake.img")); no_writes(); assert(state.closes==1);
    for (int64_t size : {-1, 0, 101}) {
        state=State{}; state.expanded=size;
        assert(!part.Flash_Sparse_Image("fake.img")); no_writes();
        assert(state.closes==1 && state.destroys==1);
    }
    for (int64_t size : {1, 100}) {
        state=State{}; state.expanded=size;
        assert(part.Flash_Sparse_Image("fake.img"));
        assert(state.output_opens==1 && state.writes==1);
#ifdef TW_ENABLE_BLKDISCARD
        assert(state.discards==1);
#else
        assert(state.discards==0);
#endif
        assert(state.closes==2 && state.destroys==1); ++cases;
    }
    state=State{}; state.output_ok=false;
    assert(!part.Flash_Sparse_Image("fake.img"));
    assert(state.output_opens==1 && state.writes==0 && state.discards==0);
    assert(state.closes==1 && state.destroys==1); ++cases;
    state=State{}; state.write_result=-1;
    assert(!part.Flash_Sparse_Image("fake.img"));
    assert(state.closes==2 && state.destroys==1); ++cases;
    state=State{}; state.sync_ok=false;
    assert(!part.Flash_Sparse_Image("fake.img")); ++cases;
    state=State{}; state.close_ok=false;
    assert(!part.Flash_Sparse_Image("fake.img")); ++cases;
    std::cout << cases << " sparse preflight cases passed\n";
}
'''
with tempfile.TemporaryDirectory(prefix='twrp-preflight-') as temp:
    cpp=Path(temp)/'test.cpp'
    cpp.write_text(prefix+method+suffix,encoding='utf-8')
    for discard in (False,True):
        exe=Path(temp)/('with-discard' if discard else 'without-discard')
        command=['g++','-std=c++17','-O0',str(cpp),'-o',str(exe)]
        if discard: command.append('-DTW_ENABLE_BLKDISCARD')
        subprocess.run(command,check=True)
        subprocess.run([str(exe)],check=True)
