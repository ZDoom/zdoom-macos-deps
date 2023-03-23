# -*- coding: utf-8 -*-
import sys
import os

import mesonbuild.mesonmain

#
sys.argv = [
    '/Volumes/ramdisk/zdoom-macos-deps/deps/meson/bin/meson',
    '--prefix=/Volumes/ramdisk/zdoom-macos-deps/build/rizin/make/rizin-v0.5.1/install_x86_64',
    '--buildtype=release',
    '--default-library=static',
    '--cross-file=/Volumes/ramdisk/zdoom-macos-deps/build/rizin/make/rizin-v0.5.1/build_x86_64/x86_64.txt',
    '/Volumes/ramdisk/zdoom-macos-deps/source/rizin/rizin-v0.5.1'
]

env = {
'PATH': '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/Apple/usr/bin',
'TMPDIR': '/Volumes/ramdisk/zdoom-macos-deps/temp/',
'CC': '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-gcc',
'CXX': '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-g++',
'CFLAGS': '-I/Volumes/ramdisk/zdoom-macos-deps/prefix/include -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'CPPFLAGS': '-I/Volumes/ramdisk/zdoom-macos-deps/prefix/include -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'CXXFLAGS': '-I/Volumes/ramdisk/zdoom-macos-deps/prefix/include -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'OBJCFLAGS': '-I/Volumes/ramdisk/zdoom-macos-deps/prefix/include -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'OBJCXXFLAGS': '-I/Volumes/ramdisk/zdoom-macos-deps/prefix/include -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'LDFLAGS': '-L/Volumes/ramdisk/zdoom-macos-deps/prefix/lib -isysroot /Volumes/ramdisk/zdoom-macos-deps/sdk/MacOSX10.12.sdk -mmacosx-version-min=10.12',
'ZERO_AR_DATE': '1',
}

for k, v in env.items():
    os.environ[k] = v
#

cwd = '/Volumes/ramdisk/zdoom-macos-deps/build/rizin/make/rizin-v0.5.1/build_x86_64'
os.makedirs(cwd, exist_ok=True)
os.chdir(cwd)

crossfile = '''
[binaries]
c = '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-gcc'
cpp = '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-g++'
objc = '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-gcc'
objcpp = '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/x86_64-apple-darwin-g++'
pkgconfig = '/Volumes/ramdisk/zdoom-macos-deps/prefix/bin/pkg-config'
strip = '/usr/bin/strip'

[host_machine]
system = 'darwin'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'
'''

if not os.path.exists('x86_64.txt'):
    with open('x86_64.txt', 'w') as f:
        f.write(crossfile)

mesonbuild.mesonmain.main()

# Fix absolute paths in r_userconf.h
search_subpath = '/Volumes/ramdisk/zdoom-macos-deps/build/rizin/make/rizin-v0.5.1/install_x86_64'
replace_subpath = '/usr/local'


def fix_paths(line: str):
    return line.replace(search_subpath, replace_subpath) if search_subpath in line else line


def update_text_file(path, processor):
    with open(path, 'r') as f:
        content = f.readlines()

    patched_content = []

    for line in content:
        patched_line = processor(line) if processor else line

        if patched_line:
            patched_content.append(patched_line)

    if content == patched_content:
        return

    file_time = os.stat(path).st_mtime

    with open(path, 'w') as f:
        f.writelines(patched_content)

    os.utime(path, (file_time, file_time))


update_text_file('rz_userconf.h', fix_paths)