#!/usr/bin/env python3
"""Compile the actual OrangeFox twrp.flags loop and exercise malformed input."""
from pathlib import Path
import subprocess
import sys
import tempfile

text = Path(sys.argv[1]).read_text()
assert 'superPartition->Can_Flash_Img = false;' in text
assert 'superPartition->Can_Flash_Img = true;' not in text
a = text.index('\t\twhile (fgets(fstab_line, sizeof(fstab_line), fstabFile) != NULL) {')
b = text.index('\n\t\tfclose(fstabFile);', a)
code = r'''
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <sstream>
#include <string>
using std::string;
#define LOGERR(...) ((void)0)
struct Flags_Map {
 string File_System, Primary_Block_Device, Alternate_Block_Device, Flags;
 char* fstab_line;
};
bool parse(FILE* fstabFile, std::map<string, Flags_Map>& twrp_flags) {
 char fstab_line[256];
''' + text[a:b] + r'''
 return true;
}
int main() {
 FILE* f = tmpfile(); assert(f);
 std::string input = "# comment\n  # indented\n\n /bad\n/short erofs\nrelative erofs system\n/comment # ignored\n";
 input += "/system_root erofs system flags=backup=0;flashimg=1\n";
 input += "  /data\tf2fs\t/dev/block/userdata flags=display=User Data;storage\n";
 input += "/duplicate ext4 old\n/duplicate erofs new\n";
 input += "/alternate emmc /dev/a /dev/b flags=backup=1\n";
 input += "/too-long erofs " + std::string(500, 'x') + "\n";
 input += "/last erofs vendor";
 fwrite(input.data(), 1, input.size(), f); rewind(f);
 std::map<string, Flags_Map> parsed;
 assert(parse(f, parsed)); fclose(f);
 assert(parsed.size() == 5);
 assert(parsed.at("/system_root").File_System == "erofs");
 assert(parsed.at("/system_root").Primary_Block_Device == "system");
 assert(parsed.at("/system_root").Flags == "flags=backup=0;flashimg=1");
 assert(parsed.at("/data").Flags == "flags=display=User Data;storage");
 assert(parsed.at("/duplicate").Primary_Block_Device == "new");
 assert(parsed.at("/alternate").Alternate_Block_Device == "/dev/b");
 assert(parsed.at("/last").Primary_Block_Device == "vendor");
 for (auto& pair : parsed) free(pair.second.fstab_line);
 puts("twrp.flags: comments, whitespace, columns, labels, malformed/overlong lines, duplicates and EOF passed");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    cpp = Path(tmp) / 'test.cpp'
    binary = Path(tmp) / 'test'
    cpp.write_text(code)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
