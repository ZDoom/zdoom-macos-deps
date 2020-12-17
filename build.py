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
import collections
import hashlib
import os
import re
import shutil
import subprocess
import typing
import urllib.request
import zipapp


class CommandLineOptions(dict):
    # Rules to combine argument's name and value
    MAKE_RULES = 0
    CMAKE_RULES = 1

    def to_list(self, rules=MAKE_RULES) -> list:
        result = []

        for arg_name, arg_value in self.items():
            if rules == CommandLineOptions.MAKE_RULES:
                option = arg_name + ('=' + arg_value if arg_value else '')
            elif rules == CommandLineOptions.CMAKE_RULES:
                arg_value = arg_value if arg_value else ''
                option = f'-D{arg_name}={arg_value}'
            else:
                assert False, 'Unknown argument rules'

            result.append(option)

        return result


class BaseTarget:
    def __init__(self, name=None):
        self.name = name

    def prepare_source(self, builder: 'Builder'):
        pass

    def initialize(self, builder: 'Builder'):
        pass

    def detect(self, builder: 'Builder') -> bool:
        return False

    def configure(self, builder: 'Builder'):
        pass

    def build(self, builder: 'Builder'):
        pass

    def post_build(self, builder: 'Builder'):
        pass


class Target(BaseTarget):
    def __init__(self, name=None):
        super().__init__(name)

        self.src_root = ''
        self.prefix = None
        self.environment = os.environ
        self.options = CommandLineOptions()

    def initialize(self, builder: 'Builder'):
        self.prefix = builder.deps_path + self.name

    def configure(self, builder: 'Builder'):
        os.makedirs(builder.build_path, exist_ok=True)

        self.environment['PATH'] = self.environment['PATH'] \
            + os.pathsep + '/Applications/CMake.app/Contents/bin' \
            + os.pathsep + builder.bin_path

        for prefix in ('CPP', 'C', 'CXX', 'OBJC', 'OBJCXX'):
            varname = f'{prefix}FLAGS'

            self._update_env(varname, f'-I{builder.include_path}')
            self._set_sdk(builder, varname)
            self._set_os_version(builder, varname)

        ldflags = 'LDFLAGS'
        self._update_env(ldflags, f'-L{builder.lib_path}')
        self._set_sdk(builder, ldflags)
        self._set_os_version(builder, ldflags)

    def _update_env(self, name: str, value: str):
        env = self.environment
        env[name] = env[name] + ' ' + value if name in env else value

    def _set_sdk(self, builder: 'Builder', varname: str):
        if builder.sdk_path:
            self._update_env(varname, f'-isysroot {builder.sdk_path}')

    def _set_os_version(self, builder: 'Builder', varname: str):
        if builder.os_version:
            self._update_env(varname, f'-mmacosx-version-min={builder.os_version}')

    def install(self, builder: 'Builder', options: 'CommandLineOptions' = None, tool: str = 'make'):
        if builder.xcode:
            return

        if os.path.exists(self.prefix):
            shutil.rmtree(self.prefix)

        args = [tool, 'install']
        args += options and options.to_list() or []

        work_path = builder.build_path + self.src_root
        subprocess.check_call(args, cwd=work_path)

        self.update_pc_files(builder)

    @staticmethod
    def update_text_file(path: str, processor: typing.Callable = None):
        with open(path, 'r') as f:
            content = f.readlines()

        patched_content = []

        for line in content:
            patched_line = processor(line) if processor else line

            if patched_line:
                patched_content.append(patched_line)

        with open(path, 'w') as f:
            f.writelines(patched_content)

    @staticmethod
    def update_prefix_shell_script(path: str, processor: typing.Callable = None):
        prefix = 'prefix='

        def update_prefix(line: str) -> str:
            if line.startswith(prefix):
                patched_line = prefix + r'"$(cd "${0%/*}/.."; pwd)"' + os.linesep
            else:
                patched_line = line

            if processor:
                patched_line = processor(patched_line)

            return patched_line

        Target.update_text_file(path, update_prefix)

    @staticmethod
    def update_pc_file(path: str, processor: typing.Callable = None):
        prefix = 'prefix='

        def pc_proc(line: str) -> str:
            patched_line = line

            if line.startswith(prefix):
                # Clear prefix variable
                patched_line = prefix + os.linesep

            if processor:
                patched_line = processor(path, patched_line)

            return patched_line

        Target.update_text_file(path, pc_proc)

    def update_pc_files(self, builder: 'Builder'):
        for root, _, files in os.walk(builder.deps_path + self.name, followlinks=True):
            for filename in files:
                if filename.endswith('.pc'):
                    file_path = root + os.sep + filename
                    Target.update_pc_file(file_path, self._process_pkg_config)

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        assert pcfile
        return line

    def write_pc_file(self, filename=None, name=None, description=None, version='',
                      requires='', requires_private='', libs='', libs_private='', cflags=''):
        pkgconfig_path = self.prefix + '/lib/pkgconfig/'
        os.makedirs(pkgconfig_path, exist_ok=True)

        if not filename:
            filename = self.name + '.pc'
        if not name:
            name = self.name
        if not description:
            description = self.name
        if not libs:
            libs = '-l' + self.name

        pc_content = f'''prefix=
exec_prefix=${{prefix}}
libdir=${{exec_prefix}}/lib
includedir=${{prefix}}/include

Name: {name}
Description: {description}
Version: {version}
Requires: {requires}
Requires.private: {requires_private}
Libs: -L${{libdir}} {libs}
Libs.private: {libs_private}
Cflags: -I${{includedir}} {cflags}
'''
        with open(pkgconfig_path + filename, 'w') as f:
            f.write(pc_content)


class MakeTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.makefile = 'Makefile'

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        Builder.symlink_directory(builder.source_path, builder.build_path)

    def build(self, builder: 'Builder'):
        assert not builder.xcode

        args = [
            'make',
            '-f', self.makefile,
            '-j', builder.jobs,
        ]
        args += self.options.to_list()

        work_path = builder.build_path + self.src_root
        subprocess.check_call(args, cwd=work_path, env=self.environment)


class ConfigureMakeTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.make = MakeTarget(name)

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self.options['--prefix'] = self.prefix

        self.make.initialize(builder)

    def configure(self, builder: 'Builder'):
        super().configure(builder)
        self.make.configure(builder)

        work_path = builder.build_path + self.src_root
        args = [work_path + os.sep + 'configure']
        args += self.options.to_list()
        subprocess.check_call(args, cwd=work_path, env=self.environment)

    def build(self, builder: 'Builder'):
        assert not builder.xcode
        self.make.build(builder)


class ConfigureMakeDependencyTarget(ConfigureMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def post_build(self, builder: 'Builder'):
        self.install(builder)


class ConfigureMakeStaticDependencyTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name=None):
        super().__init__(name)
        self.options['--enable-shared'] = 'no'


class CMakeTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)

    def detect(self, builder: 'Builder') -> bool:
        src_root = self.src_root and os.sep + self.src_root or ''
        cmakelists_path = builder.source_path + src_root + os.sep + 'CMakeLists.txt'

        if not os.path.exists(cmakelists_path):
            return False

        for line in open(cmakelists_path).readlines():
            project_name = CMakeTarget._extract_project_name(line)
            if project_name:
                project_name = project_name.lower()
                project_name = project_name.replace(' ', '-')
                break
        else:
            return False

        return project_name == self.name

    @staticmethod
    def _extract_project_name(line: str):
        project_name = None

        # Try to get project name without whitespaces in it
        match = re.search(r'project\s*\(\s*(\w[\w-]+)', line, re.IGNORECASE)

        if not match:
            # Try to get project name that contains whitespaces
            match = re.search(r'project\s*\(\s*"?(\w[\s\w-]+)"?', line, re.IGNORECASE)

        if match:
            project_name = match.group(1)

        return project_name

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        args = [
            'cmake',
            builder.xcode and '-GXcode' or '-GUnix Makefiles',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_INSTALL_PREFIX=' + self.prefix,
            '-DCMAKE_PREFIX_PATH=' + builder.prefix_path,
            '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + builder.os_version,
        ]

        if builder.sdk_path:
            args.append('-DCMAKE_OSX_SYSROOT=' + builder.sdk_path)

        args += self.options.to_list(CommandLineOptions.CMAKE_RULES)
        args.append(builder.source_path + self.src_root)

        subprocess.check_call(args, cwd=builder.build_path, env=self.environment)

    def _link_with_sound_libraries(self, builder: 'Builder'):
        extra_libs = (
            'mpg123',

            # FluidSynth with dependencies
            'fluidsynth',
            'instpatch-1.0',
            'glib-2.0',
            'gobject-2.0',
            'intl',
            'iconv',
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

        linker_args = '-framework AudioUnit -framework AudioToolbox -framework Carbon ' \
                      '-framework CoreAudio -framework CoreMIDI -framework CoreVideo'

        for lib in extra_libs:
            linker_args += f' {builder.lib_path}lib{lib}.a'

        self.options['CMAKE_EXE_LINKER_FLAGS'] = linker_args

    def build(self, builder: 'Builder'):
        if builder.xcode:
            # TODO: support case-sensitive file system
            args = ('open', self.name + '.xcodeproj')
        else:
            args = ['make', '-j', builder.jobs]

            if builder.verbose:
                args.append('VERBOSE=1')

        subprocess.check_call(args, cwd=builder.build_path)


class CMakeStaticDependencyTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

        # Set commonly used variables for static libraries
        opts = self.options
        opts['BUILD_SHARED_LIBS'] = 'NO'
        opts['ENABLE_SHARED'] = 'NO'
        opts['LIBTYPE'] = 'STATIC'

    def post_build(self, builder: 'Builder'):
        self.install(builder)


class ZDoomBaseTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        opts = self.options
        opts['PK3_QUIET_ZIPDIR'] = 'YES'
        opts['DYN_OPENAL'] = 'NO'
        # Explicit OpenAL configuration to avoid selection of Apple's framework
        opts['OPENAL_INCLUDE_DIR'] = builder.include_path + 'AL'
        opts['OPENAL_LIBRARY'] = builder.lib_path + 'libopenal.a'


class GZDoomTarget(ZDoomBaseTarget):
    def __init__(self, name='gzdoom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/coelckers/gzdoom.git')

    def post_build(self, builder: 'Builder'):
        # Put MoltenVK library into application bundle
        molten_lib = 'libMoltenVK.dylib'
        src_path = builder.lib_path + molten_lib
        dst_path = builder.build_path

        if builder.xcode:
            # TODO: Support other configurations
            dst_path += 'Debug' + os.sep

        dst_path += self.name + '.app/Contents/MacOS' + os.sep
        os.makedirs(dst_path, exist_ok=True)

        dst_path += molten_lib

        if not os.path.exists(dst_path):
            copy_func = builder.xcode and os.symlink or shutil.copy
            copy_func(src_path, dst_path)


class QZDoomTarget(GZDoomTarget):
    def __init__(self, name='qzdoom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/madame-rachelle/qzdoom.git')


class LZDoomTarget(ZDoomBaseTarget):
    def __init__(self, name='lzdoom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/drfrag666/gzdoom.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)

        opts = self.options
        opts['DYN_FLUIDSYNTH'] = 'NO'
        opts['DYN_MPG123'] = 'NO'
        opts['DYN_SNDFILE'] = 'NO'


class RazeTarget(ZDoomBaseTarget):
    def __init__(self, name='raze'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/coelckers/Raze.git')


class AccTarget(CMakeTarget):
    def __init__(self, name='acc'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/rheit/acc.git')


class PrBoomPlusTarget(CMakeTarget):
    def __init__(self, name='prboom-plus'):
        super().__init__(name)
        self.src_root = 'prboom2'

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/coelckers/prboom-plus.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        extra_linker_args = ' -framework ForceFeedback -framework IOKit'

        extra_libs = (
            'mikmod',
            'modplug',
            'opusfile',
            'webp',
        )

        for lib in extra_libs:
            extra_linker_args += f' {builder.lib_path}lib{lib}.a'

        opts = self.options
        opts['CMAKE_C_FLAGS'] = '-D_FILE_OFFSET_BITS=64'
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args
        opts['CMAKE_POLICY_DEFAULT_CMP0056'] = 'NEW'


class ChocolateDoomTarget(CMakeTarget):
    def __init__(self, name='chocolate-doom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/chocolate-doom/chocolate-doom.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        extra_linker_args = ' -lc++ -framework Cocoa -framework ForceFeedback -framework IOKit'

        extra_libs = (
            'mikmod',
            'modplug',
            'opusfile',
            'vorbisfile',
        )

        for lib in extra_libs:
            extra_linker_args += f' {builder.lib_path}lib{lib}.a'

        sdl2_include_dir = builder.include_path + 'SDL2'

        opts = self.options
        opts['SDL2_INCLUDE_DIR'] = sdl2_include_dir
        opts['SDL2_LIBRARY'] = builder.lib_path + 'libSDL2.a'
        opts['SDL2_MIXER_INCLUDE_DIR'] = sdl2_include_dir
        opts['SDL2_MIXER_LIBRARY'] = builder.lib_path + 'libSDL2_mixer.a'
        opts['SDL2_NET_INCLUDE_DIR'] = sdl2_include_dir
        opts['SDL2_NET_LIBRARY'] = builder.lib_path + 'libSDL2_net.a'
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args


class CrispyDoomTarget(ChocolateDoomTarget):
    def __init__(self, name='crispy-doom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/fabiangreffrath/crispy-doom.git')


class DoomRetroTarget(CMakeTarget):
    def __init__(self, name='doomretro'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/bradharding/doomretro.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        extra_linker_args = ' -lc++ -framework Cocoa -framework ForceFeedback -framework IOKit'

        extra_libs = (
            'mikmod',
            'modplug',
            'opusfile',
            'vorbisfile',
            'webp'
        )

        for lib in extra_libs:
            extra_linker_args += f' {builder.lib_path}lib{lib}.a'

        sdl2_include_dir = builder.include_path + 'SDL2'

        opts = self.options
        opts['SDL2_INCLUDE_DIRS'] = sdl2_include_dir
        opts['SDL2_LIBRARIES'] = builder.lib_path + 'libSDL2.a'
        opts['SDL2_FOUND'] = 'YES'
        opts['SDL2_IMAGE_INCLUDE_DIRS'] = sdl2_include_dir
        opts['SDL2_IMAGE_LIBRARIES'] = builder.lib_path + 'libSDL2_image.a'
        opts['SDL2_IMAGE_FOUND'] = 'YES'
        opts['SDL2_MIXER_INCLUDE_DIRS'] = sdl2_include_dir
        opts['SDL2_MIXER_LIBRARIES'] = builder.lib_path + 'libSDL2_mixer.a'
        opts['SDL2_MIXER_FOUND'] = 'YES'
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args


class Doom64EXTarget(CMakeTarget):
    def __init__(self, name='doom64ex'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/svkaiser/Doom64EX.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        opts = self.options
        opts['ENABLE_SYSTEM_FLUIDSYNTH'] = 'YES'
        opts['CMAKE_EXE_LINKER_FLAGS'] += ' -framework Cocoa -framework ForceFeedback -framework IOKit'


class DevilutionXTarget(CMakeTarget):
    def __init__(self, name='devilutionx'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/diasurgical/devilutionX.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)
        self._link_with_sound_libraries(builder)

        extra_linker_args = ' -framework Cocoa -framework ForceFeedback -framework IOKit'

        extra_libs = (
            'bz2',
            'freetype',
            'mikmod',
            'modplug',
            'opusfile',
            'png',
            'vorbisfile',
            'z',
        )

        for lib in extra_libs:
            extra_linker_args += f' {builder.lib_path}lib{lib}.a'

        opts = self.options
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args


class QuakespasmTarget(MakeTarget):
    def __init__(self, name='quakespasm'):
        super().__init__(name)
        self.src_root = 'Quake'

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://git.code.sf.net/p/quakespasm/quakespasm')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + os.sep + 'Quakespasm.txt')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)

        # TODO: Use macOS specific Makefile which requires manual application bundle creation
        opts = self.options
        opts['USE_SDL2'] = '1'
        opts['USE_CODEC_FLAC'] = '1'
        opts['USE_CODEC_OPUS'] = '1'
        opts['USE_CODEC_MIKMOD'] = '1'
        opts['USE_CODEC_UMX'] = '1'
        # TODO: Setup sdl2-config
        opts['SDL_CFLAGS'] = f'-I{builder.include_path}SDL2'
        opts['SDL_LIBS'] = f'{builder.lib_path}libSDL2.a'
        opts['COMMON_LIBS'] = '-framework AudioToolbox -framework Carbon -framework Cocoa -framework CoreAudio' \
            ' -framework CoreVideo -framework ForceFeedback -framework IOKit -framework OpenGL'

        self._update_env('CFLAGS', f'-I{builder.include_path}opus')
        # Use main() alias to workaround executable linking without macOS launcher
        self._update_env('LDFLAGS', f'-Wl,-alias -Wl,_SDL_main -Wl,_main')

        for name in ('opus', 'opusfile'):
            self._update_env('LDFLAGS', f'{builder.lib_path}lib{name}.a')

        # TODO: Specify full paths for remaining libraries

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        # Copy linker flags from environment to command line argument, they would be overridden by Makefile otherwise
        ldflags = 'LDFLAGS'
        self.options[ldflags] = self.environment[ldflags]


class Bzip2Target(MakeTarget):
    def __init__(self, name='bzip2'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz',
            'ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'bzlib.h')

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        # Copy compiler flags from environment to command line argument, they would be overridden by Makefile otherwise
        cflags = 'CFLAGS'
        self.options[cflags] = self.environment[cflags] + ' -D_FILE_OFFSET_BITS=64 -O2'

    def post_build(self, builder: 'Builder'):
        self.options['PREFIX'] = self.prefix
        self.install(builder, self.options)

        self.write_pc_file(description='bzip2 compression library', version='1.0.8', libs='-lbz2')


class DumbTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='dumb'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_ALLEGRO4'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/kode54/dumb/archive/2.0.3.tar.gz',
            '99bfac926aeb8d476562303312d9f47fd05b43803050cd889b44da34a9b2a4f9')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'include/dumb.h')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        if line.startswith('libdir='):
            return 'libdir=${exec_prefix}/lib\n'
        elif line.startswith('includedir='):
            return 'includedir=${prefix}/include\n'
        elif line.startswith('Libs:'):
            return 'Libs: -L${libdir} -ldumb\n'

        return line


class FfiTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ffi'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/libffi/libffi/releases/download/v3.3/libffi-3.3.tar.gz',
            '72fba7922703ddfa7a028d513ac15a85c8d54c8d67f55fa5a4802885dc652056')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libffi.pc.in')


class FlacTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='flac'):
        super().__init__(name)
        self.options['--enable-cpplibs'] = 'no'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/flac/flac-1.3.3.tar.xz',
            '213e82bd716c9de6db2f98bcadbc4c24c7e2efe8c75939a1a84e28539c4e1748')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'FLAC/flac.pc.in')


class FluidSynthTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='fluidsynth'):
        super().__init__(name)

        opts = self.options
        opts['LIB_SUFFIX'] = None
        opts['enable-framework'] = 'NO'
        opts['enable-readline'] = 'NO'
        opts['enable-sdl2'] = 'NO'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/FluidSynth/fluidsynth/archive/v2.1.5.tar.gz',
            'b539b7c65a650b56f01cd60a4e83c6125c217c5a63c0c214ef6274894a677d00')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'fluidsynth.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        if line.startswith('Version:'):
            # Add instpatch as private dependency which pulls all necessary libraries
            return line + 'Requires.private: libinstpatch-1.0' + os.linesep

        return line


class FreetypeTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='freetype'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/freetype/freetype2/2.10.4/freetype-2.10.4.tar.xz',
            '86a854d8905b19698bbc8f23b860bc104246ce4854dcea8e3b0fb21284f75784')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'include/freetype/freetype.h')


class GettextTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='gettext'):
        super().__init__(name)

        opts = self.options
        opts['--enable-csharp'] = 'no'
        opts['--enable-java'] = 'no'
        opts['--enable-libasprintf'] = 'no'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://ftp.gnu.org/gnu/gettext/gettext-0.21.tar.xz',
            'd20fcbb537e02dcf1383197ba05bd0734ef7bf5db06bdb241eb69b7d16b73192')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'gettext-runtime')


class GlibTarget(Target):
    def __init__(self, name='glib'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://download.gnome.org/sources/glib/2.66/glib-2.66.3.tar.xz',
            '79f31365a99cb1cc9db028625635d1438890702acde9e2802eae0acebcf7b5b1')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'glib.doap')

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        environment = self.environment
        environment['LDFLAGS'] += ' -framework CoreFoundation'

        args = (
            builder.bin_path + 'meson',
            '--prefix=' + builder.deps_path + self.name,
            '--buildtype=release',
            '--default-library=static',
            builder.source_path
        )
        subprocess.check_call(args, cwd=builder.build_path, env=environment)

    def build(self, builder: 'Builder'):
        args = ('ninja',)
        subprocess.check_call(args, cwd=builder.build_path, env=self.environment)

    def post_build(self, builder: 'Builder'):
        self.install(builder, tool='ninja')


class IconvTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='iconv'):
        super().__init__(name)
        self.options['--enable-extra-encodings'] = 'yes'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://ftp.gnu.org/gnu/libiconv/libiconv-1.16.tar.gz',
            'e6a1b1b589654277ee790cce3734f07876ac4ccfaecbee8afa0b649cf529cc04')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'include/iconv.h.in')


class InstPatchTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='instpatch'):
        super().__init__(name)
        self.options['LIB_SUFFIX'] = None

        # Workaround for missing frameworks in dependencies, no clue what's wrong at the moment
        self.environment['LDFLAGS'] = '-framework CoreFoundation -framework Foundation'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/swami/libinstpatch/archive/v1.1.5.tar.gz',
            '5fd01cd2ba7377e7a72caaf3b565d8fe088b5c8a14e0ea91516f0c87524bcf8a')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libinstpatch-1.0.pc.in')


class IntlTarget(GettextTarget):
    def __init__(self, name='intl'):
        super().__init__(name)
        self.src_root = 'gettext-runtime'
        self.make.src_root += self.src_root + os.sep + 'intl'

    def post_build(self, builder: 'Builder'):
        # Do install of intl only, avoid complete gettext runtime
        self.src_root = self.make.src_root
        self.install(builder)


class JpegTurboTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='jpeg-turbo'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/libjpeg-turbo/2.0.6/libjpeg-turbo-2.0.6.tar.gz',
            'd74b92ac33b0e3657123ddcf6728788c90dc84dcb6a52013d758af3c4af481bb')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'turbojpeg.h')


class MadTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mad'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/mad/libmad/0.15.1b/libmad-0.15.1b.tar.gz',
            'bbfac3ed6bfbc2823d3775ebb931087371e142bb0e9bb1bee51a76a6e0078690')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'mad.h')

    def post_build(self, builder: 'Builder'):
        super().post_build(builder)
        self.write_pc_file(description='MPEG Audio Decoder', version='0.15.1b')


class MesonTarget(Target):
    def __init__(self, name='meson'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/mesonbuild/meson/releases/download/0.56.0/meson-0.56.0.tar.gz',
            '291dd38ff1cd55fcfca8fc985181dd39be0d3e5826e5f0013bf867be40117213')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'meson.py')

    def post_build(self, builder: 'Builder'):
        script = '__main__.py'
        shutil.copy(builder.source_path + script, builder.build_path)

        module = 'mesonbuild'
        module_path = builder.build_path + module
        if os.path.exists(module_path):
            shutil.rmtree(module_path)
        shutil.copytree(builder.source_path + module, module_path)

        dest_path = builder.deps_path + self.name + os.sep + 'bin' + os.sep
        os.makedirs(dest_path, exist_ok=True)

        zipapp.create_archive(builder.build_path, dest_path + self.name, '/usr/bin/env python3', compressed=True)


class MikmodTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mikmod'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/mikmod/libmikmod/3.3.11.1/libmikmod-3.3.11.1.tar.gz',
            'ad9d64dfc8f83684876419ea7cd4ff4a41d8bcd8c23ef37ecb3a200a16b46d19')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libmikmod.pc.in')

    def post_build(self, builder: 'Builder'):
        super().post_build(builder)
        Target.update_prefix_shell_script(builder.prefix_path + '/bin/libmikmod-config')


class ModPlugTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='modplug'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/modplug-xmms/libmodplug/0.8.9.0/libmodplug-0.8.9.0.tar.gz',
            '457ca5a6c179656d66c01505c0d95fafaead4329b9dbaa0f997d00a3508ad9de')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libmodplug.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        libs_private = 'Libs.private:'

        if line.startswith(libs_private):
            return libs_private + ' -lc++\n'

        return line


class MoltenVKTarget(MakeTarget):
    def __init__(self, name='moltenvk'):
        super().__init__(name)
        self.options['macos'] = None

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/KhronosGroup/MoltenVK/archive/v1.1.1.tar.gz',
            'cd1712c571d4155f4143c435c8551a5cb8cbb311ad7fff03595322ab971682c0')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'MoltenVKPackaging.xcodeproj')

    def configure(self, builder: 'Builder'):
        # Do not use specified macOS deployment target and SDK
        # MoltenVK defines minimal OS version itself, and usually, it requires the very recent SDK
        builder.os_version = None
        builder.sdk_path = None

        super().configure(builder)

    def build(self, builder: 'Builder'):
        args = ('./fetchDependencies', '--macos', '-v')
        subprocess.check_call(args, cwd=builder.build_path)

        super().build(builder)

    def post_build(self, builder: 'Builder'):
        if builder.xcode:
            return

        if os.path.exists(self.prefix):
            shutil.rmtree(self.prefix)

        lib_path = self.prefix + os.sep + 'lib' + os.sep
        os.makedirs(lib_path)

        src_path = builder.build_path + 'Package/Latest/MoltenVK/'
        shutil.copytree(src_path + 'include', self.prefix + os.sep + 'include')
        shutil.copy(builder.build_path + 'LICENSE', self.prefix + os.sep + 'apache2.txt')

        # TODO: Replace lipo with the following line when ARM64 support will be ready
        # shutil.copy(src_path + 'dylib/macOS/libMoltenVK.dylib', lib_path)
        dylib_name = 'libMoltenVK.dylib'
        args = (
            'lipo',
            f'{src_path}dylib/macOS/{dylib_name}',
            '-thin', 'x86_64',
            '-output', lib_path + dylib_name
        )
        subprocess.check_call(args)


class Mpg123Target(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mpg123'):
        super().__init__(name)
        self.options['--enable-modules'] = 'no'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://www.mpg123.de/download/mpg123-1.26.3.tar.bz2',
            '30c998785a898f2846deefc4d17d6e4683a5a550b7eacf6ea506e30a7a736c6e')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libmpg123.pc.in')


class NasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.xz',
            '3caf6729c1073bf96629b57cee31eeb54f4f8129b01902c73428836550b30a3f')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'nasm.txt')


class NinjaTarget(MakeTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/ninja-build/ninja/archive/v1.10.2.tar.gz',
            'ce35865411f0490368a8fc383f29071de6690cbadc27704734978221f25e2bed')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'src/ninja.cc')

    def build(self, builder: 'Builder'):
        args = ('python3', './configure.py', '--bootstrap', '--verbose')
        subprocess.check_call(args, cwd=builder.build_path)

    def post_build(self, builder: 'Builder'):
        dest_path = builder.deps_path + self.name + os.sep + 'bin'
        os.makedirs(dest_path, exist_ok=True)
        shutil.copy(builder.build_path + self.name, dest_path)


class OggTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/ogg/libogg-1.3.4.tar.gz',
            'fe5670640bd49e828d64d2879c31cb4dde9758681bb664f9bdbf159a01b0c76e')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'ogg.pc.in')


class OpenALTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='openal'):
        super().__init__(name)

        opts = self.options
        opts['ALSOFT_EXAMPLES'] = 'NO'
        opts['ALSOFT_UTILS'] = 'NO'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://openal-soft.org/openal-releases/openal-soft-1.21.0.tar.bz2',
            '2916b4fc24e23b0271ce0b3468832ad8b6d8441b1830215b28cc4fee6cc89297')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'openal.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        libs_private = 'Libs.private:'

        if line.startswith(libs_private):
            # Fix full paths to OS frameworks
            return libs_private + ' -framework ApplicationServices -framework AudioToolbox'\
                                  ' -framework AudioUnit -framework CoreAudio' + os.linesep
        else:
            return line


class OpusTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opus'):
        super().__init__(name)
        self.options['--disable-extra-programs'] = None

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://archive.mozilla.org/pub/opus/opus-1.3.1.tar.gz',
            '65b58e1e25b2a114157014736a3d9dfeaad8d41be1c8179866f144a2fb44ff9d')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'opus.pc.in')


class OpusFileTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opusfile'):
        super().__init__(name)
        self.options['--enable-http'] = 'no'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/opus/opusfile-0.12.tar.gz',
            '118d8601c12dd6a44f52423e68ca9083cc9f2bfe72da7a8c1acb22a80ae3550b')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'opusfile.pc.in')


class PcreTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='pcre'):
        super().__init__(name)

        opts = self.options
        opts['--enable-unicode-properties'] = 'yes'
        opts['--enable-cpp'] = 'no'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://ftp.pcre.org/pub/pcre/pcre-8.44.tar.bz2',
            '19108658b23b3ec5058edc9f66ac545ea19f9537234be1ec62b714c84399366d')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'pcre.h.in')


class PkgConfigTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='pkg-config'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz',
            '6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'pkg-config.1')

    def post_build(self, builder: 'Builder'):
        src_path = builder.build_path + 'pkg-config'
        dst_path = builder.deps_path + self.name + os.sep + 'bin' + os.sep + 'pkg-config.exe'
        shutil.copy(src_path, dst_path)


class PngTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='png'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/libpng/libpng-1.6.37.tar.xz',
            '505e70834d35383537b6491e7ae8641f1a4bed1876dbfe361201fc80868d88ca')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libpng.pc.in')

    def post_build(self, builder: 'Builder'):
        super().post_build(builder)
        Target.update_prefix_shell_script(builder.prefix_path + '/bin/libpng16-config')


class SamplerateTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='samplerate'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'http://www.mega-nerd.com/SRC/libsamplerate-0.1.9.tar.gz',
            '0a7eb168e2f21353fb6d84da152e4512126f7dc48ccb0be80578c565413444c1')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'samplerate.pc.in')


class SndFileTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sndfile'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_REGTEST'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/libsndfile/libsndfile/releases/download/v1.0.30/libsndfile-1.0.30.tar.bz2',
            '9df273302c4fa160567f412e10cc4f76666b66281e7ba48370fb544e87e4611a')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'sndfile.pc.in')


class VorbisTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz',
            'b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'vorbis.pc.in')


class VpxTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='vpx'):
        super().__init__(name)

        opts = self.options
        opts['--disable-examples'] = None
        opts['--disable-unit-tests'] = None

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/webmproject/libvpx/archive/v1.9.0.tar.gz',
            'd279c10e4b9316bf11a570ba16c3d55791e1ad6faa4404c67422eb631782c80a')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'vpxstats.h')


class WebpTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='webp'):
        super().__init__(name)

        opts = self.options
        opts['WEBP_BUILD_ANIM_UTILS'] = 'NO'
        opts['WEBP_BUILD_CWEBP'] = 'NO'
        opts['WEBP_BUILD_DWEBP'] = 'NO'
        opts['WEBP_BUILD_GIF2WEBP'] = 'NO'
        opts['WEBP_BUILD_IMG2WEBP'] = 'NO'
        opts['WEBP_BUILD_VWEBP'] = 'NO'
        opts['WEBP_BUILD_WEBPINFO'] = 'NO'
        opts['WEBP_BUILD_WEBPMUX'] = 'NO'
        opts['WEBP_BUILD_EXTRAS'] = 'NO'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.1.0.tar.gz',
            '98a052268cc4d5ece27f76572a7f50293f439c17a98e67c4ea0c7ed6f50ef043')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'src/libwebp.pc.in')


class YasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'libyasm.h')


class ZlibTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='zlib'):
        super().__init__(name)
        self.options['--static'] = None

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://zlib.net/zlib-1.2.11.tar.gz',
            'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'zlib.pc.in')


class ZMusicTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zmusic'):
        super().__init__(name)

        opts = self.options
        opts['DYN_FLUIDSYNTH'] = 'OFF'
        opts['DYN_MPG123'] = 'OFF'
        opts['DYN_SNDFILE'] = 'OFF'

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://github.com/coelckers/ZMusic/archive/1.1.4.tar.gz',
            '29a18a6a8d0db4978a9d5badbbd612be2337d64ef0d768e944ea70f526eae285')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'include/zmusic.h')

    def post_build(self, builder: 'Builder'):
        if builder.xcode:
            return

        if os.path.exists(self.prefix):
            shutil.rmtree(self.prefix)

        lib_path = self.prefix + os.sep + 'lib' + os.sep
        os.makedirs(lib_path)

        shutil.copytree(builder.source_path + 'include', self.prefix + os.sep + 'include')

        args = (
            'libtool',
            '-static',
            '-o', lib_path + 'libzmusic.a',
            'source/libzmusic.a',
            'thirdparty/adlmidi/libadl.a',
            'thirdparty/dumb/libdumb.a',
            'thirdparty/game-music-emu/gme/libgme.a',
            'thirdparty/oplsynth/liboplsynth.a',
            'thirdparty/opnmidi/libopn.a',
            'thirdparty/timidity/libtimidity.a',
            'thirdparty/timidityplus/libtimidityplus.a',
            'thirdparty/wildmidi/libwildmidi.a',
        )
        subprocess.check_call(args, cwd=builder.build_path)

        args = (
            'libtool',
            '-static',
            '-o', lib_path + 'libzmusiclite.a',
            'source/libzmusiclite.a',
            'thirdparty/dumb/libdumb.a',
            'thirdparty/game-music-emu/gme/libgme.a',
        )
        subprocess.check_call(args, cwd=builder.build_path)


class CleanTarget(BaseTarget):
    def __init__(self, name=None):
        super().__init__(name)
        self.args = ()

    def build(self, builder: 'Builder'):
        args = ('git', 'clean') + self.args
        subprocess.check_call(args, cwd=builder.root_path)


class CleanAllTarget(CleanTarget):
    def __init__(self, name='clean-all'):
        super().__init__(name)
        self.args = ('-dX', '--force')


class CleanDepsTarget(CleanAllTarget):
    def __init__(self, name='clean-deps'):
        super().__init__(name)

    def configure(self, builder: 'Builder'):
        self.args += (builder.deps_path,)


# Case insensitive dictionary class from
# https://github.com/psf/requests/blob/v2.25.0/requests/structures.py

class CaseInsensitiveDict(collections.abc.MutableMapping):
    """A case-insensitive ``dict``-like object.
    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.
    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::
        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True
    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.
    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = collections.OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, collections.abc.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


class Builder(object):
    def __init__(self, args: list):
        self._create_targets()

        self.root_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
        self.deps_path = self.root_path + 'deps' + os.sep
        self.prefix_path = self.root_path + 'prefix' + os.sep
        self.bin_path = self.prefix_path + 'bin' + os.sep
        self.include_path = self.prefix_path + 'include' + os.sep
        self.lib_path = self.prefix_path + 'lib' + os.sep
        self.root_source_path = self.root_path + 'source' + os.sep
        self.patch_path = self.root_path + 'patch' + os.sep

        arguments = self._parse_arguments(args)

        self.xcode = arguments.xcode
        self.checkout_commit = arguments.checkout_commit
        self.build_path = arguments.build_path
        self.sdk_path = arguments.sdk_path
        self.os_version = arguments.os_version
        self.verbose = arguments.verbose

        if arguments.target:
            self.target = self.targets[arguments.target]
            self.source_path = self.root_source_path + self.target.name
        else:
            assert arguments.source_path
            self.source_path = arguments.source_path
            self._detect_target()

        if not self.build_path:
            self.build_path = self.root_path + 'build' + os.sep + self.target.name + \
                os.sep + (self.xcode and 'xcode' or 'make')

        self.source_path += os.sep
        self.build_path += os.sep

        self.jobs = arguments.jobs and arguments.jobs or \
            subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).decode('ascii').strip()

        if not self.sdk_path:
            sdk_probe_path = f'{self.root_path}sdk{os.sep}MacOSX{self.os_version}.sdk'
            if os.path.exists(sdk_probe_path):
                self.sdk_path = sdk_probe_path

        self.target.initialize(self)

    def run(self):
        self._create_prefix_directory()

        target = self.target
        target.prepare_source(self)
        target.configure(self)
        target.build(self)
        target.post_build(self)

    def _create_prefix_directory(self):
        os.makedirs(self.prefix_path, exist_ok=True)

        cleanup = True

        for dep in os.scandir(self.deps_path):
            Builder.symlink_directory(dep.path, self.prefix_path, cleanup)

            # Do symlink cleanup only once
            cleanup = False

    @staticmethod
    def symlink_directory(src_path: str, dst_path: str, cleanup=True):
        src_abspath = os.path.abspath(src_path)
        dst_abspath = os.path.abspath(dst_path)

        if cleanup:
            # Delete obsolete symbolic links
            for root, _, files in os.walk(dst_abspath, followlinks=True):
                for filename in files:
                    file_path = root + os.sep + filename

                    if os.path.islink(file_path) and not os.path.exists(file_path):
                        os.remove(file_path)

        # Create symbolic links if needed
        for entry in os.scandir(src_abspath):
            dst_subpath = entry.path.replace(src_abspath, dst_abspath)
            if entry.is_dir():
                os.makedirs(dst_subpath, exist_ok=True)
                Builder.symlink_directory(entry.path, dst_subpath, cleanup=False)
            elif not os.path.exists(dst_subpath):
                if os.path.islink(entry.path):
                    shutil.copy(entry.path, dst_subpath, follow_symlinks=False)
                else:
                    os.symlink(entry.path, dst_subpath)

    def _detect_target(self):
        for name, target in self.targets.items():
            if target.detect(self):
                self.target = self.targets[name]
                break

        assert self.target

    def _create_targets(self):
        targets = (
            GZDoomTarget(),
            QZDoomTarget(),
            LZDoomTarget(),
            RazeTarget(),
            AccTarget(),
            PrBoomPlusTarget(),
            ChocolateDoomTarget(),
            CrispyDoomTarget(),
            DoomRetroTarget(),
            Doom64EXTarget(),
            DevilutionXTarget(),
            QuakespasmTarget(),

            # Dependencies
            Bzip2Target(),
            DumbTarget(),
            FfiTarget(),
            FlacTarget(),
            FluidSynthTarget(),
            FreetypeTarget(),
            GlibTarget(),
            IconvTarget(),
            InstPatchTarget(),
            IntlTarget(),
            JpegTurboTarget(),
            MadTarget(),
            MesonTarget(),
            MikmodTarget(),
            ModPlugTarget(),
            MoltenVKTarget(),
            Mpg123Target(),
            NasmTarget(),
            NinjaTarget(),
            OggTarget(),
            OpenALTarget(),
            OpusTarget(),
            OpusFileTarget(),
            PcreTarget(),
            PkgConfigTarget(),
            PngTarget(),
            SamplerateTarget(),
            SndFileTarget(),
            VorbisTarget(),
            VpxTarget(),
            WebpTarget(),
            YasmTarget(),
            ZlibTarget(),
            ZMusicTarget(),

            # Special
            CleanAllTarget(),
            CleanDepsTarget()
        )

        self.targets = CaseInsensitiveDict({target.name: target for target in targets})

    def _parse_arguments(self, args: list):
        assert self.targets

        parser = argparse.ArgumentParser(description='*ZDoom binary dependencies for macOS')

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--target', choices=self.targets.keys(), help='target to build')
        group.add_argument('--source-path', metavar='path', help='path to target\'s source code')

        group = parser.add_argument_group()
        group.add_argument('--xcode', action='store_true', help='generate Xcode project instead of build')
        group.add_argument('--checkout-commit', metavar='commit',
                           help='target\'s source code commit or tag to checkout')
        group.add_argument('--build-path', metavar='path', help='target build path')
        group.add_argument('--sdk-path', metavar='path', help='path to macOS SDK')
        group.add_argument('--os-version', metavar='version', default='10.9', help='macOS deployment version')
        group.add_argument('--verbose', action='store_true', help='enable verbose build output')
        group.add_argument('--jobs', help='number of parallel compilation jobs')

        return parser.parse_args(args)

    def checkout_git(self, url: str):
        if not os.path.exists(self.source_path):
            args = ('git', 'clone', '--recurse-submodules', url, self.source_path)
            subprocess.check_call(args, cwd=self.root_path)

        if self.checkout_commit:
            args = ['git', 'checkout', self.checkout_commit]
            subprocess.check_call(args, cwd=self.source_path)

    def _read_source_package(self, url: str) -> (bytes, str):
        filename = url.rsplit(os.sep, 1)[1]
        filepath = self.source_path + filename

        if os.path.exists(filepath):
            # Read existing source package
            with open(filepath, 'rb') as f:
                data = f.read()
        else:
            # Download package with source code
            print(f'Downloading {filename}')

            response = urllib.request.urlopen(url)

            try:
                with open(filepath, 'wb') as f:
                    data = response.read()
                    f.write(data)

            except IOError:
                os.unlink(filepath)
                raise

        return data, filepath

    @staticmethod
    def _verify_checksum(checksum: str, data: bytes, filepath: str) -> None:
        file_hasher = hashlib.sha256()
        file_hasher.update(data)
        file_checksum = file_hasher.hexdigest()

        if file_checksum != checksum:
            os.unlink(filepath)
            raise Exception(f'Checksum of {filepath} does not match, expected: {checksum}, actual: {file_checksum}')

    def _unpack_source_package(self, filepath: str) -> (str, str):
        filepaths = subprocess.check_output(['tar', '-tf', filepath]).decode("utf-8")
        filepaths = filepaths.split('\n')
        first_path_component = None

        for path in filepaths:
            if os.sep in path:
                first_path_component = path[:path.find(os.sep)]
                break

        if not first_path_component:
            raise Exception("Failed to figure out source code path for " + filepath)

        extract_path = self.source_path + first_path_component + os.sep

        if not os.path.exists(extract_path):
            # Extract source code package
            try:
                subprocess.check_call(['tar', '-xf', filepath], cwd=self.source_path)
            except (IOError, subprocess.CalledProcessError):
                shutil.rmtree(extract_path, ignore_errors=True)
                raise

        return first_path_component, extract_path

    def _apply_source_patch(self, extract_path: str):
        patch_path = self.patch_path + self.target.name + '.patch'

        if not os.path.exists(patch_path):
            return

        # Check if patch is already applied
        test_arg = '--dry-run'
        args = ['patch', test_arg, '--strip=1', '--input=' + patch_path]

        if subprocess.call(args, cwd=extract_path) == 0:
            # Patch wasn't applied yet, do it now
            args.remove(test_arg)
            subprocess.check_call(args, cwd=extract_path)

    def download_source(self, url: str, checksum: str):
        os.makedirs(self.source_path, exist_ok=True)

        data, filepath = self._read_source_package(url)
        Builder._verify_checksum(checksum, data, filepath)

        first_path_component, extract_path = self._unpack_source_package(filepath)
        self._apply_source_patch(extract_path)

        # Adjust source and build paths according to extracted source code
        self.source_path = extract_path
        self.build_path = self.build_path + first_path_component + os.sep


if __name__ == '__main__':
    Builder(sys.argv[1:]).run()
