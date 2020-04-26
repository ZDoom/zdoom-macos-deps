#!/usr/bin/env python3

#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020 Alexey Lysiuk
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys

if sys.hexversion < 0x3070000:
    print('Build module requires Python 3.7 or newer')
    exit(1)


import argparse
import re
import os
import shutil
import subprocess
import tarfile


class Configuration(object):
    def __init__(self):
        self.root_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
        self.deps_path = self.root_path + 'deps' + os.sep
        self.prefix_path = self.root_path + 'prefix' + os.sep
        self.include_path = self.prefix_path + 'include' + os.sep
        self.lib_path = self.prefix_path + 'lib' + os.sep

        self.target = None
        self.xcode = False
        self.checkout_commit = None
        self.generate = True
        self.rebuild_prefix = False
        self.create_package = False

        self.source_path = None
        self.build_path = None
        self.sdk_path = None


class Target(object):
    def __init__(self, name: str, url: str, post_build=None):
        self.name = name
        self.url = url
        self.post_build = post_build


def copy_moltenvk(config: Configuration):
    molten_lib = 'libMoltenVK.dylib'
    src_path = config.lib_path + molten_lib
    dst_path = config.build_path

    if config.xcode:
        dst_path += 'Debug' + os.sep

    dst_path += config.target.name + '.app/Contents/MacOS' + os.sep
    os.makedirs(dst_path, exist_ok=True)

    dst_path += molten_lib

    if not os.path.exists(dst_path):
        copy_func = config.xcode and os.symlink or shutil.copy
        copy_func(src_path, dst_path)


def detect_target(config: Configuration, targets: dict):
    cmakelists_path = config.source_path + os.sep + 'CMakeLists.txt'
    project_name = None

    for line in open(cmakelists_path).readlines():
        match = re.search(r'project\s*\(\s*(\w+)\s*\)', line, re.IGNORECASE)
        if match:
            project_name = match.group(1).lower()
            break

    assert project_name
    config.target = targets[project_name]


def create_configuration(args: list):
    target_list = (
        Target('gzdoom', 'https://github.com/coelckers/gzdoom.git', copy_moltenvk),
        Target('qzdoom', 'https://github.com/madame-rachelle/qzdoom.git', copy_moltenvk),
        Target('lzdoom', 'https://github.com/drfrag666/gzdoom.git'),
        Target('raze', 'https://github.com/coelckers/Raze.git'),
    )
    targets = {target.name: target for target in target_list}

    parser = argparse.ArgumentParser(description='*ZDoom binary dependencies for macOS')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--target', choices=targets.keys(), help='target to build')
    group.add_argument('--source-path', metavar='path', help='path to target\'s source code')

    group = parser.add_argument_group()
    group.add_argument('--xcode', action='store_true', help='generate Xcode project instead of build')
    group.add_argument('--checkout-commit', metavar='commit', help='target\'s source code commit or tag to checkout')
    group.add_argument('--build-path', metavar='path', help='target build path')
    group.add_argument('--sdk-path', metavar='path', help='path to macOS SDK')
    group.add_argument('--skip-generate', action='store_true', help='do not generate build environment')
    group.add_argument('--create-package', action='store_true', help='create deployment package')
    group.add_argument('--rebuild-prefix', action='store_true', help='rebuild prefix path')

    arguments = parser.parse_args(args)

    config = Configuration()
    config.xcode = arguments.xcode
    config.checkout_commit = arguments.checkout_commit
    config.generate = not arguments.skip_generate
    config.rebuild_prefix = arguments.rebuild_prefix
    config.build_path = arguments.build_path
    config.sdk_path = arguments.sdk_path
    config.create_package = arguments.create_package

    if arguments.target:
        config.target = targets[arguments.target]
        config.source_path = config.root_path + config.target.name
    else:
        assert arguments.source_path
        config.source_path = arguments.source_path
        detect_target(config, targets)

    if not config.build_path:
        config.build_path = config.root_path + 'build' + os.sep + config.target.name + \
            os.sep + (config.xcode and 'xcode' or 'make')

    config.source_path += os.sep
    config.build_path += os.sep

    return config


def create_prefix_directory(config: Configuration):
    if os.path.exists(config.prefix_path):
        if config.rebuild_prefix:
            shutil.rmtree(config.prefix_path)
        else:
            return

    os.makedirs(config.include_path)
    os.makedirs(config.lib_path)

    for dep in os.scandir(config.deps_path):
        if not dep.is_dir():
            continue

        dep_include_path = dep.path + os.sep + 'include' + os.sep
        dep_lib_path = dep.path + os.sep + 'lib' + os.sep

        if not os.path.exists(dep_include_path) or not os.path.exists(dep_lib_path):
            continue

        for dep_include in os.scandir(dep_include_path):
            os.symlink(dep_include.path, config.include_path + dep_include.name)

        for dep_lib in os.scandir(dep_lib_path):
            os.symlink(dep_lib.path, config.lib_path + dep_lib.name)


def prepare_source(config: Configuration):
    if not os.path.exists(config.source_path):
        args = ('git', 'clone', config.target.url, config.source_path)
        subprocess.check_call(args, cwd=config.root_path)

    if config.checkout_commit:
        args = ['git', 'checkout', config.checkout_commit]
        subprocess.check_call(args, cwd=config.source_path)


def generate_cmake(config: Configuration):
    if not config.generate:
        return

    environ = os.environ
    environ['PATH'] = environ['PATH'] + os.pathsep + '/Applications/CMake.app/Contents/bin'

    os.makedirs(config.build_path, exist_ok=True)

    extra_libs = (
        'mpg123',

        # FluidSynth with dependencies
        'fluidsynth',
        'instpatch-1.0',
        'glib-2.0',
        'gobject-2.0',
        'intl',
        'ffi',
        'pcre',
        
        # Sndfile with dependencies
        'sndfile',
        'ogg',
        'vorbis',
        'vorbisenc',
        'FLAC',
        'opus',
    )

    linker_args = '-framework AudioUnit -framework AudioToolbox -framework Carbon -framework CoreAudio ' \
                  '-framework CoreMIDI -framework CoreVideo -framework ForceFeedback -liconv'

    for lib in extra_libs:
        linker_args += f' {config.lib_path}lib{lib}.a'

    args = [
        'cmake',
        config.xcode and '-GXcode' or '-GUnix Makefiles',
        '-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_PREFIX_PATH=' + config.prefix_path,
        '-DCMAKE_EXE_LINKER_FLAGS=' + linker_args,
        '-DFORCE_INTERNAL_ZLIB=YES',
        '-DFORCE_INTERNAL_BZIP2=YES',
        '-DPK3_QUIET_ZIPDIR=YES',
        '-DDYN_OPENAL=NO',
        # Explicit OpenAL configuration to avoid selection of Apple's framework
        '-DOPENAL_INCLUDE_DIR=' + config.include_path,
        '-DOPENAL_LIBRARY=' + config.lib_path + 'libopenal.a',
    ]

    if config.sdk_path:
        args.append('-DCMAKE_OSX_SYSROOT=' + config.sdk_path)

    args.append(config.source_path)

    subprocess.check_call(args, cwd=config.build_path, env=environ)


def build_target(config: Configuration):
    if config.xcode:
        # TODO: support case-sensitive file system
        args = ('open', config.target.name + '.xcodeproj')
    else:
        jobs = subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).decode('ascii').strip()
        args = ('make', '-j', jobs)

    subprocess.check_call(args, cwd=config.build_path)

    if config.target.post_build:
        config.target.post_build(config)


def create_package(config: Configuration):
    if not config.create_package or config.xcode:
        return

    args = ['git', 'describe', '--tags']
    version = subprocess.check_output(args, cwd=config.source_path).decode('ascii').strip()
    package_path = f'{config.build_path}{config.target.name}-{version}.tar.bz2'
    name_pos = len(config.build_path) - 1

    if os.path.exists(package_path):
        os.remove(package_path)

    def tar_filter(tarinfo):
        tarinfo.name = tarinfo.name[name_pos:]
        tarinfo.uname = tarinfo.gname = "root"
        tarinfo.uid = tarinfo.gid = 0
        return tarinfo

    with tarfile.open(package_path, 'w:bz2') as package:
        bundle_path = config.build_path + config.target.name + '.app'
        package.add(bundle_path, filter=tar_filter)


def build(args: list):
    config = create_configuration(args)
    create_prefix_directory(config)

    prepare_source(config)
    generate_cmake(config)
    build_target(config)
    create_package(config)


if __name__ == '__main__':
    build(sys.argv[1:])
