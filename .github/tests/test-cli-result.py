#!/usr/bin/env python3
"""Compile the patched CLI and dispatcher; use temporary FIFOs and mocked ORS."""
from pathlib import Path
import subprocess, tempfile, sys, threading, os, time
root=Path(sys.argv[1]).resolve()
def compile_cpp(source, output, include):
    subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-I",str(include),str(source),"-o",str(output)],check=True)
with tempfile.TemporaryDirectory(prefix="twrp-cli-test-") as temp:
    p=Path(temp)
    (p/"sys").mkdir()
    (p/"sys/capability.h").write_text("#include <linux/capability.h>\n")
    (p/"variables.h").write_text('#define TW_VERSION_STR "test"\n')
    (p/"orscmd").mkdir()
    client=(root/"orscmd/orscmd.cpp").read_text()
    (p/"orscmd/orscmd.cpp").write_text(client)
    (p/"orscmd/orscmd.h").write_text('#define ORS_INPUT_FILE "'+str(p/"input")+'"\n#define ORS_OUTPUT_FILE "'+str(p/"output")+'"\n')
    binary=p/"twrp"
    compile_cpp(p/"orscmd/orscmd.cpp",binary,p)
    for args in [["print","x"*511],["print","first\nreboot"],["getcap",str(p/"absent")]]:
        r=subprocess.run([str(binary),*args],capture_output=True,timeout=3)
        assert r.returncode != 0, args
    cases=[
        (b"",b"\0TW\0",0),
        (b"Installer finished\n",b"\0TW\0",0),
        (b"ERROR 42\n",b"\0TW\1",1),
        (b"Failed, operation in progress\n",b"\0TW\1",1),
        (b"Installer crashed",b"",1),
        (b"",b"",1),
        (b"partial",b"\0T",1),
        (b"wrong",b"\0TW\7",1),
        (b"x"*16003+b"\n",b"\0TW\0",0),
    ]
    for chunk in [1,3,512,4096]:
        for payload,footer,status in cases:
            for name in ["input","output"]:
                path=p/name
                if path.exists(): path.unlink()
                os.mkfifo(path)
            errors=[]
            def server():
                try:
                    with open(p/"input","rb",buffering=0) as incoming:
                        command=incoming.read(1024)
                        assert command == b"print test\0", repr(command)
                        with open(p/"output","wb",buffering=0) as outgoing:
                            data=payload+footer
                            for offset in range(0,len(data),chunk):
                                outgoing.write(data[offset:offset+chunk])
                except Exception as exc: errors.append(exc)
            thread=threading.Thread(target=server,daemon=True)
            thread.start()
            r=subprocess.run([str(binary),"print","test"],capture_output=True,timeout=10)
            thread.join(2)
            assert not thread.is_alive() and not errors, errors
            assert r.returncode==status, (chunk,payload,r)
            expected=payload if footer in [b"\0TW\0",b"\0TW\1"] else payload+footer
            assert r.stdout==expected,(chunk,len(payload),r.stdout[:80])
    # Compile the real dispatcher with the production class declaration.
    (p/"openrecoveryscript.hpp").write_text((root/"openrecoveryscript.hpp").read_text())
    source=(root/"openrecoveryscript.cpp").read_text()
    start=source.index("int OpenRecoveryScript::Run_CLI_Command(")
    end=source.index("int OpenRecoveryScript::remountrw",start)
    harness=r"""
#include <cassert>
#include <string>
#include <vector>
#include <sstream>
#include <cstdlib>
#include "openrecoveryscript.hpp"
int result=0, copies=1, inserted=1, calls=0, last=-1;
#define LOGINFO(...) ((void)0)
#define gui_print_color(...) ((void)0)
#define gui_print(...) ((void)0)
#define gui_err(...) ((void)0)
#define gui_msg(...) ((void)0)
struct TWFunc {
 static std::vector<std::string> Split_String(std::string s, const char*) {
  std::vector<std::string> v; std::istringstream in(s); std::string x;
  while(in>>x) v.push_back(x);
  return v;
 }
 static std::string get_log_dir(){ return "/tmp"; }
 static bool Path_Exists(std::string){ return false; }
};
struct DataManager { static int GetValue(std::string, std::string&){ return result; } };
struct PM { int Decrypt_Device(std::string,int){ return result; } } PartitionManager;
OpenRecoveryScript::VoidFunction OpenRecoveryScript::call_after_cli_command;
int OpenRecoveryScript::copy_script_file(std::string){return copies;}
int OpenRecoveryScript::run_script_file(bool){++calls; return result;}
int OpenRecoveryScript::Insert_ORS_Command(std::string){return inserted;}
int OpenRecoveryScript::Run_OpenRecoveryScript_Action(){return result;}
void done(int status){last=status;}
"""
    finish_start=source.index("\tif (sideload && !cli)")
    finish_end=source.index("\n}",finish_start)
    harness+="int finish_sideload(int ret_val, bool sideload, bool cli) {\n"+source[finish_start:finish_end]+"\n}\n"
    harness+=source[start:end]
    harness+=r"""
int main(){
 OpenRecoveryScript::Call_After_CLI_Command(done);
 for(int code : {0,1,42,-1}) {
  result=code;
  for(auto cmd : {"install /tmp/test.zip","runscript /tmp/test.ors","get test","getval test","decrypt dummy"}) {
   last=-1; assert(OpenRecoveryScript::Run_CLI_Command(cmd)==(code!=0));
   assert(last==(code!=0));
  }
 }
 result=0; copies=0; inserted=0;
 for(auto cmd : {"runscript /tmp/missing","runscript","get","decrypt",""}) {
  last=-1; assert(OpenRecoveryScript::Run_CLI_Command(cmd)==1); assert(last==1);
 }
 assert(calls==8);
 for(auto cmd : {"console_message hello", "console_warning hello", "console_error hello"}) {
  assert(OpenRecoveryScript::Run_CLI_Command(cmd)==0); assert(last==0);
 }
 for(auto cmd : {"console_message", "console_warning", "console_error", "getval"}) {
  assert(OpenRecoveryScript::Run_CLI_Command(cmd)==1); assert(last==1);
 }
 assert(finish_sideload(0,true,true)==0);
 assert(finish_sideload(1,true,true)==1);
 assert(finish_sideload(0,true,false)==1);
 assert(finish_sideload(0,false,false)==0);
 inserted=1; result=0; assert(OpenRecoveryScript::Run_CLI_Command("")==1);
}
"""
    (p/"dispatch.cpp").write_text(harness)
    compile_cpp(p/"dispatch.cpp",p/"dispatch",p)
    subprocess.run([str(p/"dispatch")],check=True)
    # Compile the real GUI completion and action code with minimal GUI stubs.
    gui=(root/"gui/gui.cpp").read_text()
    a=gui.index("static void ors_command_done(int status)")
    b=gui.index("static void ors_command_read()",a)
    action=(root/"gui/action.cpp").read_text()
    c=action.index("int GUIAction::twcmd(")
    d=action.index("int GUIAction::getKeyByName",c)
    code=r"""
#include <cassert>
#include <cstdio>
#include <string>
#include <unistd.h>
FILE* orsout=nullptr;
int ors_read_fd=-1, resets=0, ended=-1, command_status=0;
void gui_set_FILE(FILE*){}
void setup_ors_command(){++resets;}
struct DataManager {static int GetIntValue(const char*){return 0;}};
struct OpenRecoveryScript {static int Run_CLI_Command(const char*){return command_status;}};
struct GUIAction {
 bool simulate=false;
 void operation_start(const char*){}
 void simulate_progress_bar(){}
 void operation_end(int status){ended=status;}
 int twcmd(std::string);
};
"""
    code+=gui[a:b]+action[c:d]
    code+=r"""
int main(){
 for(int status : {0,1,42}) {
  orsout=tmpfile(); assert(orsout);
  int copy=dup(fileno(orsout)); assert(copy>=0);
  fputs("test\n",orsout);
  ors_command_done(status);
  assert(orsout==nullptr);
  lseek(copy,0,SEEK_SET);
  unsigned char buffer[16]={};
  assert(read(copy,buffer,sizeof(buffer))==9);
  assert(buffer[5]==0 && buffer[6]=='T' && buffer[7]=='W' && buffer[8]==(status!=0));
  close(copy);
 }
 assert(resets==3);
 GUIAction action;
 for(int status : {0,1}) {
  command_status=status; action.twcmd("test"); assert(ended==status);
 }
}
"""
    (p/"gui-test.cpp").write_text(code)
    compile_cpp(p/"gui-test.cpp",p/"gui-test",p)
    subprocess.run([str(p/"gui-test")],check=True)
print("CLI: 36 FIFO scenarios, local error cases, dispatcher, sideload and GUI completion/action checks passed")
