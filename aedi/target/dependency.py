#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020-2021 Alexey Lysiuk
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

import os
import shutil
import subprocess
import zipapp

from .base import BuildTarget, MakeTarget, ConfigureMakeTarget, CMakeTarget
from ..state import BuildState


class ConfigureMakeDependencyTarget(ConfigureMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def post_build(self, state: BuildState):
        self.install(state)


class ConfigureMakeStaticDependencyTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name=None):
        super().__init__(name)

        self.options['--enable-shared'] = 'no'


class CMakeStaticDependencyTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

        # Set commonly used variables for static libraries
        opts = self.options
        opts['BUILD_SHARED_LIBS'] = 'NO'
        opts['ENABLE_SHARED'] = 'NO'
        opts['LIBTYPE'] = 'STATIC'

    def post_build(self, state: BuildState):
        self.install(state)


class Bzip2Target(MakeTarget):
    def __init__(self, name='bzip2'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz',
            'ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'bzlib.h')

    def configure(self, state: BuildState):
        super().configure(state)

        opts = self.options
        # Add explicit targets in order to skip testing step that is incompatible with cross-compilation
        opts['bzip2'] = None
        opts['bzip2recover'] = None
        # Copy compiler flags from environment to command line argument, they would be overridden by Makefile otherwise
        cflags = 'CFLAGS'
        opts[cflags] = self.environment[cflags] + ' -D_FILE_OFFSET_BITS=64 -O2'

    def post_build(self, state: BuildState):
        self.options['PREFIX'] = state.install_path
        self.install(state, self.options)

        self.write_pc_file(state, description='bzip2 compression library', version='1.0.8', libs='-lbz2')


class DumbTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='dumb'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_ALLEGRO4'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/kode54/dumb/archive/2.0.3.tar.gz',
            '99bfac926aeb8d476562303312d9f47fd05b43803050cd889b44da34a9b2a4f9')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/dumb.h')

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

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libffi/libffi/releases/download/v3.3/libffi-3.3.tar.gz',
            '72fba7922703ddfa7a028d513ac15a85c8d54c8d67f55fa5a4802885dc652056')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libffi.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)

        for header in ('ffi.h', 'ffitarget.h'):
            self.make_platform_header(state, header)


class FlacTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='flac'):
        super().__init__(name)
        self.options['--enable-cpplibs'] = 'no'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.xiph.org/releases/flac/flac-1.3.3.tar.xz',
            '213e82bd716c9de6db2f98bcadbc4c24c7e2efe8c75939a1a84e28539c4e1748')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'FLAC/flac.pc.in')


class FluidSynthTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='fluidsynth'):
        super().__init__(name)

        opts = self.options
        opts['LIB_SUFFIX'] = None
        opts['enable-framework'] = 'NO'
        opts['enable-readline'] = 'NO'
        opts['enable-sdl2'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/FluidSynth/fluidsynth/archive/v2.1.6.tar.gz',
            '328fc290b5358544d8dea573f81cb1e97806bdf49e8507db067621242f3f0b8a')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'fluidsynth.pc.in')

    def configure(self, state: BuildState):
        # TODO: Figure out why private dependencies aren't pulled
        self.options['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'glib-2.0')
        super().configure(state)

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        if line.startswith('Version:'):
            # Add instpatch as private dependency which pulls all necessary libraries
            return line + 'Requires.private: libinstpatch-1.0' + os.linesep
        elif line.startswith('Libs:'):
            # Add missing system frameworks to link with
            return line + 'Libs.private: -framework AudioUnit -framework CoreAudio -framework CoreMIDI' + os.linesep

        return line


class FreetypeTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='freetype'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/freetype/freetype2/2.10.4/freetype-2.10.4.tar.xz',
            '86a854d8905b19698bbc8f23b860bc104246ce4854dcea8e3b0fb21284f75784')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/freetype/freetype.h')


class GettextTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='gettext'):
        super().__init__(name)

        opts = self.options
        opts['--enable-csharp'] = 'no'
        opts['--enable-java'] = 'no'
        opts['--enable-libasprintf'] = 'no'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/gettext/gettext-0.21.tar.xz',
            'd20fcbb537e02dcf1383197ba05bd0734ef7bf5db06bdb241eb69b7d16b73192')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'gettext-runtime')


class GlibTarget(BuildTarget):
    def __init__(self, name='glib'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.gnome.org/sources/glib/2.66/glib-2.66.4.tar.xz',
            '97df8670e32f9fd4f7392b0980e661dd625012015d58350da1e58e343f4af984')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'glib.doap')

    def configure(self, state: BuildState):
        super().configure(state)

        environment = self.environment
        environment['LDFLAGS'] += ' -framework CoreFoundation'

        cpu = state.architecture()
        cpu_family = 'arm' if 'arm64' == cpu else cpu

        cross_file = state.build_path + state.architecture() + '.txt'
        with open(cross_file, 'w') as f:
            f.write(f'''
[binaries]
c = '{state.c_compiler()}'
cpp = '{state.cxx_compiler()}'
objc = '{state.c_compiler()}'
objcpp = '{state.cxx_compiler()}'
pkgconfig = '{state.prefix_path}/bin/pkg-config'
strip = '/usr/bin/strip'

[host_machine]
system = 'darwin'
cpu_family = '{cpu_family}'
cpu = '{cpu}'
endian = 'little'
''')

        args = (
            state.bin_path + 'meson',
            '--prefix=' + state.install_path,
            '--buildtype=release',
            '--default-library=static',
            '--cross-file=' + cross_file,
            state.source
        )
        subprocess.check_call(args, cwd=state.build_path, env=environment)

    def build(self, state: BuildState):
        args = ('ninja',)
        subprocess.check_call(args, cwd=state.build_path, env=self.environment)

    def post_build(self, state: BuildState):
        self.install(state, tool='ninja')


class GmakeTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='gmake'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/make/make-4.3.tar.lz',
            'de1a441c4edf952521db30bfca80baae86a0ff1acd0a00402999344f04c45e82')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'doc/make.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, 'make', self.name)


class IconvTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='iconv'):
        super().__init__(name)
        self.options['--enable-extra-encodings'] = 'yes'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/libiconv/libiconv-1.16.tar.gz',
            'e6a1b1b589654277ee790cce3734f07876ac4ccfaecbee8afa0b649cf529cc04')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/iconv.h.in')


class InstPatchTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='instpatch'):
        super().__init__(name)
        self.options['LIB_SUFFIX'] = None

        # Workaround for missing frameworks in dependencies, no clue what's wrong at the moment
        self.environment['LDFLAGS'] = '-framework CoreFoundation -framework Foundation'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/swami/libinstpatch/archive/v1.1.6.tar.gz',
            '8e9861b04ede275d712242664dab6ffa9166c7940fea3b017638681d25e10299')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libinstpatch-1.0.pc.in')


class IntlTarget(GettextTarget):
    def __init__(self, name='intl'):
        super().__init__(name)
        self.src_root = 'gettext-runtime'
        self.make.src_root += self.src_root + os.sep + 'intl'

    def post_build(self, state: BuildState):
        # Do install of intl only, avoid complete gettext runtime
        self.src_root = self.make.src_root
        self.install(state)


class JpegTurboTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='jpeg-turbo'):
        super().__init__(name)
        self.options['WITH_TURBOJPEG'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/libjpeg-turbo/2.0.6/libjpeg-turbo-2.0.6.tar.gz',
            'd74b92ac33b0e3657123ddcf6728788c90dc84dcb6a52013d758af3c4af481bb')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'turbojpeg.h')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        if line.startswith('exec_prefix='):
            return 'exec_prefix=${prefix}\n'
        elif line.startswith('libdir='):
            return 'libdir=${exec_prefix}/lib\n'
        elif line.startswith('includedir='):
            return 'includedir=${prefix}/include\n'

        return line


class MadTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mad'):
        super().__init__(name)
        self.options['--enable-fpm'] = '64bit'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/mad/libmad/0.15.1b/libmad-0.15.1b.tar.gz',
            'bbfac3ed6bfbc2823d3775ebb931087371e142bb0e9bb1bee51a76a6e0078690')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'mad.h')

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.write_pc_file(state, description='MPEG Audio Decoder', version='0.15.1b')


class MesonTarget(BuildTarget):
    def __init__(self, name='meson'):
        super().__init__(name)
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/mesonbuild/meson/releases/download/0.56.0/meson-0.56.0.tar.gz',
            '291dd38ff1cd55fcfca8fc985181dd39be0d3e5826e5f0013bf867be40117213')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'meson.py')

    def post_build(self, state: BuildState):
        script = '__main__.py'
        shutil.copy(state.source + script, state.build_path)

        module = 'mesonbuild'
        module_path = state.build_path + module
        if os.path.exists(module_path):
            shutil.rmtree(module_path)
        shutil.copytree(state.source + module, module_path)

        dest_path = state.install_path + 'bin' + os.sep
        os.makedirs(dest_path, exist_ok=True)

        zipapp.create_archive(state.build_path, dest_path + self.name, '/usr/bin/env python3', compressed=True)


class MikmodTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mikmod'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/mikmod/libmikmod/3.3.11.1/libmikmod-3.3.11.1.tar.gz',
            'ad9d64dfc8f83684876419ea7cd4ff4a41d8bcd8c23ef37ecb3a200a16b46d19')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libmikmod.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.update_prefix_shell_script(state.install_path + '/bin/libmikmod-config')


class ModPlugTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='modplug'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/modplug-xmms/libmodplug/0.8.9.0/libmodplug-0.8.9.0.tar.gz',
            '457ca5a6c179656d66c01505c0d95fafaead4329b9dbaa0f997d00a3508ad9de')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libmodplug.pc.in')

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
        # Building for multiple architectures is handled internally
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/MoltenVK/archive/v1.1.1.tar.gz',
            'cd1712c571d4155f4143c435c8551a5cb8cbb311ad7fff03595322ab971682c0')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'MoltenVKPackaging.xcodeproj')

    def configure(self, state: BuildState):
        # Unset platform to avoid using specified macOS deployment target and SDK
        # MoltenVK defines minimal OS version itself, and usually, it requires the very recent SDK
        state.platform = None

        super().configure(state)

    def build(self, state: BuildState):
        args = ('./fetchDependencies', '--macos', '-v')
        subprocess.check_call(args, cwd=state.build_path)

        super().build(state)

    def post_build(self, state: BuildState):
        if state.xcode:
            return

        if os.path.exists(state.install_path):
            shutil.rmtree(state.install_path)

        lib_path = state.install_path + os.sep + 'lib' + os.sep
        os.makedirs(lib_path)

        src_path = state.build_path + 'Package/Latest/MoltenVK/'
        shutil.copytree(src_path + 'include', state.install_path + os.sep + 'include')
        shutil.copy(state.build_path + 'LICENSE', state.install_path + os.sep + 'apache2.txt')
        shutil.copy(src_path + 'dylib/macOS/libMoltenVK.dylib', lib_path)


class Mpg123Target(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mpg123'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.mpg123.de/download/mpg123-1.26.4.tar.bz2',
            '081991540df7a666b29049ad870f293cfa28863b36488ab4d58ceaa7b5846454')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libmpg123.pc.in')


class NasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.xz',
            '3caf6729c1073bf96629b57cee31eeb54f4f8129b01902c73428836550b30a3f')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'nasm.txt')


class NinjaTarget(MakeTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ninja-build/ninja/archive/v1.10.2.tar.gz',
            'ce35865411f0490368a8fc383f29071de6690cbadc27704734978221f25e2bed')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'src/ninja.cc')

    def build(self, state: BuildState):
        cmdlines = (
            ('python3', './configure.py', '--verbose'),
            ('ninja', '--verbose'),
        )

        for args in cmdlines:
            subprocess.run(args, check=True, cwd=state.build_path, env=self.environment)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class OggTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.xiph.org/releases/ogg/libogg-1.3.4.tar.gz',
            'fe5670640bd49e828d64d2879c31cb4dde9758681bb664f9bdbf159a01b0c76e')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'ogg.pc.in')


class OpenALTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='openal'):
        super().__init__(name)

        opts = self.options
        opts['ALSOFT_EXAMPLES'] = 'NO'
        opts['ALSOFT_UTILS'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://openal-soft.org/openal-releases/openal-soft-1.21.0.tar.bz2',
            '2916b4fc24e23b0271ce0b3468832ad8b6d8441b1830215b28cc4fee6cc89297')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'openal.pc.in')

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

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://archive.mozilla.org/pub/opus/opus-1.3.1.tar.gz',
            '65b58e1e25b2a114157014736a3d9dfeaad8d41be1c8179866f144a2fb44ff9d')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'opus.pc.in')


class OpusFileTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opusfile'):
        super().__init__(name)
        self.options['--enable-http'] = 'no'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.xiph.org/releases/opus/opusfile-0.12.tar.gz',
            '118d8601c12dd6a44f52423e68ca9083cc9f2bfe72da7a8c1acb22a80ae3550b')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'opusfile.pc.in')


class PcreTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='pcre'):
        super().__init__(name)

        opts = self.options
        opts['--enable-unicode-properties'] = 'yes'
        opts['--enable-cpp'] = 'no'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.pcre.org/pub/pcre/pcre-8.44.tar.bz2',
            '19108658b23b3ec5058edc9f66ac545ea19f9537234be1ec62b714c84399366d')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'pcre.h.in')


class PkgConfigTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='pkg-config'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz',
            '6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'pkg-config.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, new_filename=self.name + '.exe')


class PngTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='png'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/libpng/libpng-1.6.37.tar.xz',
            '505e70834d35383537b6491e7ae8641f1a4bed1876dbfe361201fc80868d88ca')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libpng.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.update_prefix_shell_script(state.install_path + '/bin/libpng16-config')


class PortMidiTarget(CMakeTarget):
    def __init__(self, name='portmidi'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/portmedia/portmidi/217/portmidi-src-217.zip',
            '08e9a892bd80bdb1115213fb72dc29a7bf2ff108b378180586aa65f3cfd42e0f')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'pm_common/portmidi.h')

    def post_build(self, state: BuildState):
        if os.path.exists(state.install_path):
            shutil.rmtree(state.install_path)

        include_path = state.install_path + os.sep + 'include'
        os.makedirs(include_path)
        shutil.copy(state.source + 'pm_common/portmidi.h', include_path)
        shutil.copy(state.source + 'porttime/porttime.h', include_path)

        lib_path = state.install_path + os.sep + 'lib' + os.sep
        os.makedirs(lib_path)
        shutil.copy(state.build_path + 'libportmidi_s.a', lib_path + 'libportmidi.a')


class SamplerateTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='samplerate'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsamplerate/releases/download/0.2.1/libsamplerate-0.2.1.tar.bz2',
            'f6323b5e234753579d70a0af27796dde4ebeddf58aae4be598e39b3cee00c90a')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'samplerate.pc.in')


class Sdl2Target(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2'):
        super().__init__(name)

        # Need to have uniform settings for x86_64 and arm64 because of linking with Metal framework
        # TODO: Remove this when default target for x64 will become 10.11+
        opts = self.options
        opts['VIDEO_VULKAN'] = 'NO'
        opts['VIDEO_METAL'] = 'NO'
        opts['RENDER_METAL'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://libsdl.org/release/SDL2-2.0.14.tar.gz',
            'd8215b571a581be1332d2106f8036fcb03d12a70bae01e20f424976d275432bc')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'sdl2.pc.in')

    LINKER_FLAGS = ' -L${libdir} -lSDL2'\
        ' -framework AudioToolbox -framework AVFoundation -framework Carbon -framework Cocoa'\
        ' -framework CoreAudio -framework CoreFoundation -framework CoreVideo'\
        ' -framework ForceFeedback -framework Foundation -framework IOKit\n'

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_libs(line: str):
            if line.startswith('      echo -L${exec_prefix}/lib'):
                return '      echo' + Sdl2Target.LINKER_FLAGS

            return line

        self.update_prefix_shell_script(state.install_path + '/bin/sdl2-config', update_libs)
        self.make_platform_header(state, 'SDL2/SDL_config.h')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        libs = 'Libs:'

        if line.startswith(libs):
            return libs + Sdl2Target.LINKER_FLAGS

        return line


class Sdl2ImageTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_image'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.5.tar.gz',
            'bdd5f6e026682f7d7e1be0b6051b209da2f402a2dd8bd1c4bd9c25ad263108d0')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'SDL2_image.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        return line + 'Requires.private: libwebp\n' if line.startswith('Requires:') else line


class Sdl2MixerTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_mixer'):
        super().__init__(name)
        self.options['--enable-music-mod-mikmod'] = 'yes'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.0.4.tar.gz',
            'b4cf5a382c061cd75081cf246c2aa2f9df8db04bdda8dcdc6b6cca55bede2419')

    def configure(self, state: BuildState):
        # Set LDFLAGS explicitly to help with FluidSynth and FLAC detection
        self.environment['LDFLAGS'] = state.run_pkg_config('--libs', 'fluidsynth')

        super().configure(state)

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'SDL2_mixer.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        if line.startswith('Requires:'):
            return line + 'Requires.private: fluidsynth libmikmod libmodplug libmpg123 opusfile vorbisfile\n'

        return line


class Sdl2NetTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_net'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_net/release/SDL2_net-2.0.1.tar.gz',
            '15ce8a7e5a23dafe8177c8df6e6c79b6749a03fff1e8196742d3571657609d21')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'SDL2_net.pc.in')


class Sdl2TtfTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_ttf'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.15.tar.gz',
            'a9eceb1ad88c1f1545cd7bd28e7cbc0b2c14191d40238f531a15b01b1b22cd33')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'SDL2_ttf.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        return line + 'Requires.private: freetype2\n' if line.startswith('Requires:') else line


class SndFileTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sndfile'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_REGTEST'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsndfile/releases/download/v1.0.30/libsndfile-1.0.30.tar.bz2',
            '9df273302c4fa160567f412e10cc4f76666b66281e7ba48370fb544e87e4611a')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'sndfile.pc.in')


class SodiumTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sodium'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.libsodium.org/libsodium/releases/libsodium-1.0.18.tar.gz',
            '6f504490b342a4f8a4c4a02fc9b866cbef8622d5df4e5452b46be121e46636c1')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libsodium.pc.in')


class VorbisTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz',
            'b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'vorbis.pc.in')


class VpxTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='vpx'):
        super().__init__(name)

        opts = self.options
        opts['--disable-examples'] = None
        opts['--disable-unit-tests'] = None

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/webmproject/libvpx/archive/v1.9.0.tar.gz',
            'd279c10e4b9316bf11a570ba16c3d55791e1ad6faa4404c67422eb631782c80a')

    def configure(self, state: BuildState):
        hosts = {
            'x86_64': 'x86_64-darwin13-gcc',
            'arm64': 'arm64-darwin20-gcc',
        }
        self.options['--target'] = hosts[state.architecture()]

        super().configure(state)

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'vpxstats.h')


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

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.1.0.tar.gz',
            '98a052268cc4d5ece27f76572a7f50293f439c17a98e67c4ea0c7ed6f50ef043')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'src/libwebp.pc.in')


class YasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libyasm.h')


class ZlibTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='zlib'):
        super().__init__(name)
        self.options['--static'] = None

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://zlib.net/zlib-1.2.11.tar.gz',
            'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'zlib.pc.in')


class ZMusicTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zmusic'):
        super().__init__(name)

        opts = self.options
        opts['DYN_FLUIDSYNTH'] = 'OFF'
        opts['DYN_MPG123'] = 'OFF'
        opts['DYN_SNDFILE'] = 'OFF'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/coelckers/ZMusic/archive/1.1.4.tar.gz',
            '29a18a6a8d0db4978a9d5badbbd612be2337d64ef0d768e944ea70f526eae285')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/zmusic.h')

    def post_build(self, state: BuildState):
        if state.xcode:
            return

        if os.path.exists(state.install_path):
            shutil.rmtree(state.install_path)

        lib_path = state.install_path + os.sep + 'lib' + os.sep
        os.makedirs(lib_path)

        shutil.copytree(state.source + 'include', state.install_path + os.sep + 'include')

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
        subprocess.check_call(args, cwd=state.build_path)

        args = (
            'libtool',
            '-static',
            '-o', lib_path + 'libzmusiclite.a',
            'source/libzmusiclite.a',
            'thirdparty/dumb/libdumb.a',
            'thirdparty/game-music-emu/gme/libgme.a',
        )
        subprocess.check_call(args, cwd=state.build_path)
