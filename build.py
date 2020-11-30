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
import urllib.request


class CommandLineOptions(dict):
    def to_list(self, prefix='') -> list:
        result = []

        for arg_name, arg_value in self.items():
            option = prefix + arg_name
            option += arg_value and ('=' + arg_value) or ''
            result.append(option)

        return result


class Target:
    def __init__(self, name=None):
        self.name = name
        self.src_root = ''
        self.prefix = None
        self.environment = os.environ
        self.options = CommandLineOptions()

    def prepare_source(self, builder: 'Builder'):
        pass

    def initialize(self, builder: 'Builder'):
        self.prefix = builder.deps_path + self.name

    def detect(self, builder: 'Builder') -> bool:
        return False

    def configure(self, builder: 'Builder'):
        os.makedirs(builder.build_path, exist_ok=True)

        self.environment['PATH'] = self.environment['PATH'] \
            + os.pathsep + '/Applications/CMake.app/Contents/bin' \
            + os.pathsep + builder.bin_path
        self.environment['PKG_CONFIG_PATH'] = builder.lib_path + 'pkgconfig'

    def build(self, builder: 'Builder'):
        pass

    def post_build(self, builder: 'Builder'):
        pass

    def install(self, builder: 'Builder'):
        if builder.xcode:
            return

        if os.path.exists(self.prefix):
            shutil.rmtree(self.prefix)

        work_path = builder.build_path + self.src_root
        subprocess.check_call(['make', 'install'], cwd=work_path)


class MakeTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.makefile = 'Makefile'

    def configure(self, builder: 'Builder'):
        super().configure(builder)

        Builder.symlink_directory(builder.source_path, builder.build_path)

        for prefix in ('CPP', 'C', 'CXX', 'OBJC', 'OBJCXX'):
            varname = f'{prefix}FLAGS'

            self._update_env(varname, f'-I{builder.include_path}')
            self._set_sdk(builder, varname)
            self._set_os_version(builder, varname)

        ldflags = 'LDFLAGS'
        self._update_env(ldflags, f'-L{builder.lib_path}')
        self._set_sdk(builder, ldflags)
        self._set_os_version(builder, ldflags)

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

    def _update_env(self, name: str, value: str):
        env = self.environment
        env[name] = env[name] + ' ' + value if name in env else value

    def _set_sdk(self, builder: 'Builder', varname: str):
        if builder.sdk_path:
            self._update_env(varname, f'-isysroot {builder.sdk_path}')

    def _set_os_version(self, builder: 'Builder', varname: str):
        if builder.os_version:
            self._update_env(varname, f'-mmacosx-version-min={builder.os_version}')


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

    def build(self, builder: 'Builder'):
        assert not builder.xcode

        work_path = builder.build_path + self.src_root
        args = [work_path + os.sep + 'configure']
        args += self.options.to_list()
        subprocess.check_call(args, cwd=work_path, env=self.environment)

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

        args += self.options.to_list('-D')
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


class CMakeStaticDependencyTarget(Target):
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
        opts['OPENAL_INCLUDE_DIR'] = builder.include_path
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


class ZandronumTarget(CMakeTarget):
    def __init__(self, name='zandronum'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        # TODO: use official Mercurial repository
        builder.checkout_git('https://github.com/TorrSamaho/zandronum.git')

    def initialize(self, builder: 'Builder'):
        super().initialize(builder)

        opts = self.options
        opts['CMAKE_EXE_LINKER_FLAGS'] = '-framework AudioUnit -framework Carbon -framework IOKit'
        # TODO: Linking to FluidSynth is disabled because Zandronum doesn't support FluidSynth 2.x
        # opts['DYN_FLUIDSYNTH'] = 'NO'
        opts['FMOD_INCLUDE_DIR'] = builder.include_path
        opts['FMOD_LIBRARY'] = builder.lib_path + 'libfmodex.dylib'


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


class JpegTurboTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='jpeg-turbo'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.sourceforge.net/project/libjpeg-turbo/2.0.6/libjpeg-turbo-2.0.6.tar.gz',
            'd74b92ac33b0e3657123ddcf6728788c90dc84dcb6a52013d758af3c4af481bb')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'turbojpeg.h')


class NasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.xz',
            '3caf6729c1073bf96629b57cee31eeb54f4f8129b01902c73428836550b30a3f')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'nasm.txt')


class OggTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/ogg/libogg-1.3.4.tar.gz',
            'fe5670640bd49e828d64d2879c31cb4dde9758681bb664f9bdbf159a01b0c76e')

        test_arg = '--dry-run'
        os_types_path = builder.source_path + 'include/ogg/os_types.h'
        patch_path = builder.root_source_path + 'ogg.patch'
        args = ['patch', test_arg, os_types_path, patch_path]

        if subprocess.call(args) == 0:
            args.remove(test_arg)
            subprocess.check_call(args)

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'ogg.pc.in')


class OpusTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opus'):
        super().__init__(name)

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


class VorbisTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.download_source(
            'https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz',
            'b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b')

    def detect(self, builder: 'Builder') -> bool:
        return os.path.exists(builder.source_path + 'vorbis.pc.in')


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
            ZandronumTarget(),
            AccTarget(),
            PrBoomPlusTarget(),
            ChocolateDoomTarget(),
            CrispyDoomTarget(),
            DoomRetroTarget(),
            Doom64EXTarget(),
            DevilutionXTarget(),
            QuakespasmTarget(),

            # Dependencies
            JpegTurboTarget(),
            NasmTarget(),
            OggTarget(),
            OpusTarget(),
            OpusFileTarget(),
            VorbisTarget(),
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

    def download_source(self, url: str, checksum: str):
        source_path = self.source_path
        os.makedirs(source_path, exist_ok=True)

        filename = source_path + url.rsplit(os.sep, 1)[1]

        if os.path.exists(filename):
            # Read existing source package
            with open(filename, 'rb') as f:
                data = f.read()
        else:
            # Download package with source code
            response = urllib.request.urlopen(url)

            try:
                with open(filename, 'wb') as f:
                    data = response.read()
                    f.write(data)

            except IOError:
                os.unlink(filename)
                raise

        # Verify package checksum
        file_hasher = hashlib.sha256()
        file_hasher.update(data)
        file_checksum = file_hasher.hexdigest()

        if file_checksum != checksum:
            os.unlink(filename)
            raise Exception(f'Checksum of {filename} does not match, expected: {checksum}, actual: {file_checksum}')

        # Figure out path to extracted source code
        filepaths = subprocess.check_output(['tar', '-tf', filename]).decode("utf-8")
        filepaths = filepaths.split('\n')
        first_path_component = None

        for filepath in filepaths:
            if os.sep in filepath:
                first_path_component = filepath[:filepath.find(os.sep)]
                break

        if not first_path_component:
            raise Exception("Failed to figure out source code path for " + filename)

        extract_path = source_path + first_path_component

        if not os.path.exists(extract_path):
            # Extract source code package
            try:
                subprocess.check_call(['tar', '-xf', filename], cwd=source_path)
            except (IOError, subprocess.CalledProcessError):
                shutil.rmtree(extract_path, ignore_errors=True)
                raise

        # Adjust source and build paths according to extracted source code
        self.source_path = extract_path + os.sep
        self.build_path = self.build_path + first_path_component + os.sep


if __name__ == '__main__':
    Builder(sys.argv[1:]).run()
