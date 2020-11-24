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

import collections
import argparse
import re
import os
import shutil
import subprocess


class Target:
    def __init__(self, name=None):
        self.name = name
        self.src_root = ''
        self.cmake_options = {}

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
        environ = os.environ
        environ['PATH'] = environ['PATH'] \
            + os.pathsep + '/Applications/CMake.app/Contents/bin' \
            + os.pathsep + builder.bin_path
        environ['PKG_CONFIG_PATH'] = builder.lib_path + 'pkgconfig'

        os.makedirs(builder.build_path, exist_ok=True)

        args = [
            'cmake',
            builder.xcode and '-GXcode' or '-GUnix Makefiles',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_PREFIX_PATH=' + builder.prefix_path,
            '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + builder.os_version,
        ]

        if builder.sdk_path:
            args.append('-DCMAKE_OSX_SYSROOT=' + builder.sdk_path)

        for cmake_arg_name, cmake_arg_value in self.cmake_options.items():
            args.append(f'-D{cmake_arg_name}={cmake_arg_value}')

        args.append(builder.source_path + self.src_root)

        subprocess.check_call(args, cwd=builder.build_path, env=environ)

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

        self.cmake_options['CMAKE_EXE_LINKER_FLAGS'] = linker_args

    def build(self, builder: 'Builder'):
        if builder.xcode:
            # TODO: support case-sensitive file system
            args = ('open', self.name + '.xcodeproj')
        else:
            args = ['make', '-j', builder.jobs]

            if builder.verbose:
                args.append('VERBOSE=1')

        subprocess.check_call(args, cwd=builder.build_path)


class ZDoomBaseTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def initialize(self, builder: 'Builder'):
        self._link_with_sound_libraries(builder)

        opts = self.cmake_options
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

        opts = self.cmake_options
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
        opts = self.cmake_options
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

        opts = self.cmake_options
        opts['CMAKE_C_FLAGS'] = '-D_FILE_OFFSET_BITS=64'
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args
        opts['CMAKE_POLICY_DEFAULT_CMP0056'] = 'NEW'


class ChocolateDoomTarget(CMakeTarget):
    def __init__(self, name='chocolate-doom'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/chocolate-doom/chocolate-doom.git')

    def initialize(self, builder: 'Builder'):
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

        opts = self.cmake_options
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

        opts = self.cmake_options
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
        self._link_with_sound_libraries(builder)

        opts = self.cmake_options
        opts['ENABLE_SYSTEM_FLUIDSYNTH'] = 'YES'
        opts['CMAKE_EXE_LINKER_FLAGS'] += ' -framework Cocoa -framework ForceFeedback -framework IOKit'


class DevilutionXTarget(CMakeTarget):
    def __init__(self, name='devilutionx'):
        super().__init__(name)

    def prepare_source(self, builder: 'Builder'):
        builder.checkout_git('https://github.com/diasurgical/devilutionX.git')

    def initialize(self, builder: 'Builder'):
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

        opts = self.cmake_options
        opts['CMAKE_EXE_LINKER_FLAGS'] += extra_linker_args


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

        arguments = self._parse_arguments(args)

        self.xcode = arguments.xcode
        self.checkout_commit = arguments.checkout_commit
        self.build_path = arguments.build_path
        self.sdk_path = arguments.sdk_path
        self.os_version = arguments.os_version
        self.verbose = arguments.verbose

        if arguments.target:
            self.target = self.targets[arguments.target]
            self.source_path = self.root_path + 'source' + os.sep + self.target.name
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
        os.makedirs(self.bin_path, exist_ok=True)
        os.makedirs(self.include_path, exist_ok=True)
        os.makedirs(self.lib_path, exist_ok=True)

        # Delete obsolete symbolic links
        for root, _, files in os.walk(self.prefix_path, followlinks=True):
            for filename in files:
                file_path = root + os.sep + filename

                if os.path.islink(file_path) and not os.path.exists(file_path):
                    os.remove(file_path)

        # Create symbolic links if needed
        for dep in os.scandir(self.deps_path):
            if not dep.is_dir():
                continue

            def symlink_deps(src_dir):
                src_path = dep.path + os.sep + src_dir + os.sep
                if not os.path.exists(src_path):
                    return

                dst_path = self.prefix_path + src_dir + os.sep

                for src in os.scandir(src_path):
                    dst_subpath = dst_path + src.name

                    if src.is_dir():
                        os.makedirs(dst_subpath, exist_ok=True)
                        symlink_deps(src_dir + os.sep + src.name)
                    elif not os.path.exists(dst_subpath):
                        os.symlink(src.path, dst_subpath)

            symlink_deps('bin')
            symlink_deps('include')
            symlink_deps('lib')

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


if __name__ == '__main__':
    Builder(sys.argv[1:]).run()
