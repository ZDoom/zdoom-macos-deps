#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys


class Configuration(object):
    def __init__(self):
        self.root_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
        self.deps_path = self.root_path + 'deps' + os.sep
        self.prefix_path = self.root_path + 'prefix' + os.sep
        self.include_path = self.prefix_path + 'include' + os.sep
        self.lib_path = self.prefix_path + 'lib' + os.sep

        self.target = None
        self.xcode = False
        self.commit = None

        self.source_path = None
        self.build_path = None


class Target(object):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


def create_configuration():
    target_list = (
        Target('gzdoom', 'https://github.com/coelckers/gzdoom.git'),
        Target('raze', 'https://github.com/coelckers/Raze.git'),
    )
    targets = {target.name: target for target in target_list}

    parser = argparse.ArgumentParser(description='*ZDoom binary dependencies for macOS')
    parser.add_argument('target', choices=targets.keys(), help='target to build')
    parser.add_argument('--xcode', action='store_true', help='generate Xcode project instead of build')
    parser.add_argument('--commit', help='target\'s commit or tag to checkout')
    arguments = parser.parse_args()

    config = Configuration()
    config.target = targets[arguments.target]
    config.xcode = arguments.xcode
    config.commit = arguments.commit
    config.source_path = config.root_path + config.target.name
    config.build_path = config.root_path + 'build' + os.sep + config.target.name + \
        os.sep + (config.xcode and 'xcode' or 'make')

    return config


def create_prefix_directory(config: Configuration):
    if os.path.exists(config.prefix_path):
        shutil.rmtree(config.prefix_path)

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

    args = ['git', 'checkout', config.commit and config.commit or 'master']
    subprocess.check_call(args, cwd=config.source_path)


def generate_cmake(config: Configuration):
    environ = os.environ
    environ['PATH'] = environ['PATH'] + os.pathsep + '/Applications/CMake.app/Contents/bin'

    if not os.path.exists(config.build_path):
        os.makedirs(config.build_path)

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

    args = (
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
        config.source_path
    )
    subprocess.check_call(args, cwd=config.build_path, env=environ)


def build_target(config: Configuration):
    if config.xcode:
        # TODO: support case-sensitive file system
        args = ('open', config.target.name + '.xcodeproj')
    else:
        jobs = subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).decode('ascii').strip()
        args = ('make', '-j', jobs)

    subprocess.check_call(args, cwd=config.build_path)


def main():
    config = create_configuration()
    create_prefix_directory(config)

    prepare_source(config)
    generate_cmake(config)
    build_target(config)


if __name__ == '__main__':
    if sys.hexversion < 0x3070000:
        print('This script requires Python 3.7 or newer')
        exit(1)

    main()
