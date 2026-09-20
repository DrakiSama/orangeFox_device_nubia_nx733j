#!/usr/bin/env python3
"""Compile the actual logical IMG helpers and dispatch with simulated device I/O."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text(encoding='utf-8')
start = source.index('// NX733J: keep this lock alive')
end = source.index('\nbool TWPartition::Is_Sparse_Image', start)
methods = source[start:end]
prefix = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <filesystem>
#include <functional>
#include <iostream>
#include <string>
#include <vector>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <linux/fs.h>
constexpr uint32_t SPARSE_HEADER_MAGIC=0xed26ff3a;
struct State {
 bool lock_ok=true, state_ok=true, dir_ok=true, snapshots=false, dir_error=false;
 bool map_ok=true, table_ok=true, mapped_same=true, direct=true;
 bool input_ok=true, input_regular=true, import_ok=true, target_ok=true, target_block=true;
 bool ioctl_ok=true, read_only=false, output_ok=true, output_same=true;
 bool read_ok=true, write_ok=true, sync_ok=true, sparse=false;
 int64_t length=16, expanded=16;
 uint64_t capacity=32;
 std::string ota="", type="linear";
 int writes=0, output_opens=0, destroys=0, syncs=0, reads=0, lock_held=0;
} state;
int fake_open(const char* path, int flags) {
 std::string p(path);
 if(p=="/metadata/ota") { if(!state.lock_ok) return -1; ++state.lock_held; return 3; }
 if(p=="/image.img") return state.input_ok ? 4 : -1;
 if((flags & O_ACCMODE)==O_WRONLY) {
  assert(state.lock_held==1);
  assert((flags & O_EXCL) && !(flags & (O_TRUNC|O_CREAT)));
  ++state.output_opens; return state.output_ok ? 6 : -1;
 }
 return state.target_ok ? 5 : -1;
}
int fake_close(int fd) { if(fd==3) --state.lock_held; return 0; }
int fake_flock(int,int) { return state.lock_ok ? 0 : -1; }
DIR* fake_opendir(const char*) { return state.dir_ok ? reinterpret_cast<DIR*>(1) : nullptr; }
dirent* fake_readdir(DIR*) { static dirent entry{}; strcpy(entry.d_name,"system_b"); errno=state.dir_error ? EIO : 0; return state.snapshots ? &entry : nullptr; }
int fake_closedir(DIR*) { return 0; }
int fake_stat(const char* path, struct stat* st) {
 st->st_mode=S_IFBLK; st->st_rdev=makedev(253,1);
 if(std::string(path)=="mapped" && !state.mapped_same) st->st_rdev=makedev(253,2);
 if(std::string(path)=="/dev/block/by-name/super") st->st_rdev=makedev(8,7);
 return 0;
}
int fake_fstat(int fd, struct stat* st) {
 st->st_mode=state.target_block ? S_IFBLK : S_IFREG;
 st->st_rdev=makedev(253, fd==6 && !state.output_same ? 2 : 1);
 if(fd==4) {st->st_mode=state.input_regular ? S_IFREG : S_IFBLK; st->st_size=state.length;}
 return 0;
}
int fake_ioctl(int, unsigned long request, void* value) {
 if(!state.ioctl_ok) return -1;
 if(request==BLKGETSIZE64) *static_cast<uint64_t*>(value)=state.capacity;
 else *static_cast<int*>(value)=state.read_only;
 return 0;
}
off_t fake_lseek(int,off_t,int) {return 0;}
int fake_fsync(int) {++state.syncs; return state.sync_ok ? 0 : -1;}
namespace android { namespace base {
 class unique_fd {
  int fd_;
 public:
  unique_fd(int fd=-1):fd_(fd){}
  unique_fd(const unique_fd&)=delete;
  unique_fd(unique_fd&& other):fd_(other.fd_){other.fd_=-1;}
  ~unique_fd(){if(fd_>=0) fake_close(fd_);}
  bool ok() const{return fd_>=0;} int get() const{return fd_;}
 };
 struct guard {std::function<void()> fn; ~guard(){fn();}};
 template<class F> guard make_scope_guard(F f){return {f};}
 bool ReadFileToString(const std::string&,std::string* text){*text=state.ota;return state.state_ok;}
 bool ReadFully(int,void* out,size_t count){
  if(!state.read_ok) return false;
  if(state.reads++==0 && count==4) *static_cast<uint32_t*>(out)=state.sparse ? SPARSE_HEADER_MAGIC : 0;
  return true;
 }
 bool WriteFully(int,const void*,size_t){++state.writes;return state.write_ok;}
} namespace dm {
 class DeviceMapper {
 public:
  struct TargetInfo {struct {char target_type[32];} spec; std::string data;};
  static DeviceMapper& Instance(){static DeviceMapper dm;return dm;}
  bool GetDmDevicePathByName(const std::string& name,std::string* path){assert(name=="system_b");*path="mapped";return state.map_ok;}
  bool GetTableInfo(const std::string&,std::vector<TargetInfo>* table){
   TargetInfo t{};strcpy(t.spec.target_type,state.type.c_str());t.data=state.direct ? "8:7 123" : "253:4 123";
   table->push_back(t);return state.table_ok;
  }
 };
}}
struct sparse_file {};
sparse_file object;
sparse_file* sparse_file_import(int,bool,bool){return state.import_ok ? &object : nullptr;}
int64_t sparse_file_len(sparse_file*,bool,bool){return state.expanded;}
void sparse_file_destroy(sparse_file*){++state.destroys;}
int sparse_file_write(sparse_file*,int,bool,bool,bool){++state.writes;return state.write_ok ? 0 : -1;}
struct Msg {template<class... T> Msg(T...){} template<class... T> Msg operator()(T...){return *this;}};
#define gui_err(...) ((void)0)
#define gui_msg(...) ((void)0)
#define LOGINFO(...) ((void)0)
int access(const char*, int) { return 0; }
#ifndef R_OK
#define R_OK 4
#endif
#define LOGERR(...) ((void)0)
struct Progress {void UpdateSize(uint64_t){} void UpdateDisplayDetails(bool){}};
struct PartitionSettings {std::string Backup_Folder="";bool adbbackup=false;Progress* progress=nullptr;};
using std::string;
enum BackupMethod {BM_FILES,BM_DD,BM_FLASH_UTILS};
class TWPartition {
public:
 bool Is_Super=true, Can_Flash_Img=true, mounted=false, unmount_ok=true;
 uint64_t Size=32;
 BackupMethod Backup_Method=BM_FILES;
 std::string Backup_FileName="image.img", Mount_Point="/system_root", Actual_Block_Device="device",Display_Name="System";
 bool Flash_Image_FI(const std::string&, void*) { return false; }
 bool Flash_Image(PartitionSettings*);
 bool Is_Mounted(){return mounted;}
 bool UnMount(bool){if(unmount_ok) mounted=false;return unmount_ok;}
 bool Find_Partition_Size(){return true;}
 bool Is_Sparse_Image(const std::string&){return state.sparse;}
 bool Flash_Sparse_Image(const std::string&){return true;}
 bool Raw_Read_Write(PartitionSettings*){return true;}
};
TWPartition metadata;
struct PM {
 TWPartition* Find_Partition_By_Path(const std::string&){return &metadata;}
 std::string Get_Active_Slot_Suffix(){return "_b";}
} PartitionManager;
namespace TWFunc {uint64_t Get_File_Size(const std::string&){return state.length;}}
#define AB_OTA_UPDATER
#define open fake_open
#define flock fake_flock
#define opendir fake_opendir
#define readdir fake_readdir
#define closedir fake_closedir
#define stat(...) fake_stat(__VA_ARGS__)
#define fstat fake_fstat
#define ioctl fake_ioctl
#define lseek fake_lseek
#define fsync fake_fsync
'''
suffix = r'''
int main(){
 int cases=0;
 auto run=[&](std::function<void(TWPartition&,PartitionSettings&)> configure, bool expected, bool before_open=true){
  state=State{};metadata.mounted=true;TWPartition part;PartitionSettings settings;
  configure(part,settings);
  assert(part.Flash_Image(&settings)==expected);
  assert(state.lock_held==0);
  assert(part.Backup_Method==BM_FILES);
  if(!expected && before_open) assert(state.output_opens==0 && state.writes==0);
  ++cases;
 };
 run([](auto&,auto&){},true);
 assert(state.writes==1 && state.syncs==1);
 run([](auto&,auto&){state.sparse=true;},true);assert(state.destroys==1);
 run([](auto&,auto&){state.length=32;},true);
 run([](auto&,auto&){state.ota="none";},true);
 for(std::string ota:{"initiated","unverified","merging","merge-completed","cancelled","garbage"})
  run([&](auto&,auto&){state.ota=ota;},false);
 for(std::string type:{"snapshot","snapshot-merge","user","verity"})
  run([&](auto&,auto&){state.type=type;},false);
 for(auto member:{&State::lock_ok,&State::state_ok,&State::dir_ok,&State::map_ok,&State::table_ok,
                  &State::mapped_same,&State::direct,&State::input_ok,&State::input_regular,
                  &State::target_ok,&State::target_block,&State::ioctl_ok,&State::read_ok})
  run([&](auto&,auto&){state.*member=false;},false);
 for(auto member:{&State::snapshots,&State::dir_error,&State::read_only})
  run([&](auto&,auto&){state.*member=true;},false);
 for(int64_t length:{0,3,33}) run([&](auto&,auto&){state.length=length;},false);
 for(int64_t expanded:{-1,0,33}) {
  run([&](auto&,auto&){state.sparse=true;state.expanded=expanded;},false);
  assert(state.destroys==1);
 }
 run([](auto&,auto&){state.sparse=true;state.import_ok=false;},false);
 run([](auto&,auto&){metadata.mounted=false;},false);
 run([](auto& p,auto&){p.Can_Flash_Img=false;},false);
 run([](auto&,auto& s){s.adbbackup=true;},false);
 run([](auto& p,auto&){p.unmount_ok=false;},false);
 for(auto member:{&State::output_ok,&State::output_same,&State::write_ok,&State::sync_ok})
  run([&](auto&,auto&){state.*member=false;},false,false);
 run([](auto&,auto&){state.sparse=true;state.write_ok=false;},false,false);assert(state.destroys==1);
 run([](auto& p,auto&){p.Is_Super=false;},false);
 std::cout<<cases<<" logical image cases passed (simulated I/O)\n";
}
'''
with tempfile.TemporaryDirectory() as temp:
    cpp = Path(temp) / 'test.cpp'
    binary = Path(temp) / 'test'
    cpp.write_text(prefix + methods + suffix, encoding='utf-8')
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
