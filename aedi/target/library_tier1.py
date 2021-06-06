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

import re

from .base import *
from ..state import BuildState


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


class FlacTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='flac'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_CXXLIBS'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'
        opts['OGG_PACKAGE'] = 'ogg'
        opts['VERSION'] = '1.3.3'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/flac/flac-1.3.3.tar.xz',
            '213e82bd716c9de6db2f98bcadbc4c24c7e2efe8c75939a1a84e28539c4e1748',
            patches='flac-fix-cmake')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'FLAC/flac.pc.in')

    def configure(self, state: BuildState):
        self.options['CMAKE_EXE_LINKER_FLAGS'] = '-framework CoreFoundation -L' + state.lib_path
        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        shutil.copytree(state.install_path + 'share/FLAC/cmake', state.install_path + 'lib/cmake/FLAC')
        shutil.copytree(state.install_path + 'share/pkgconfig', state.install_path + 'lib/pkgconfig')

        self.keep_module_target(state, 'FLAC::FLAC')


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
            'https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v2.2.1.tar.gz',
            '1c56660f23f6c406b36646cc619fc2d2a5265d1d3290e79bcef4505bcd985fdd')

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
            'https://downloads.sourceforge.net/project/libjpeg-turbo/2.1.0/libjpeg-turbo-2.1.0.tar.gz',
            'bef89803e506f27715c5627b1e3219c95b80fc31465d4452de2a909d382e4444')

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


class MoltenVKTarget(MakeTarget):
    def __init__(self, name='moltenvk'):
        super().__init__(name)
        self.options['macos'] = None
        # Building for multiple architectures is handled internally
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/MoltenVK/archive/v1.1.3.tar.gz',
            'c20758bc19a46060aaf6e0949b47d29824b70b9ec0e22fb73a3feeef4c73a0ef')

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


class Mpg123Target(CMakeStaticDependencyTarget):
    def __init__(self, name='mpg123'):
        super().__init__(name)

        self.src_root = 'ports/cmake'
        self.options['CMAKE_EXE_LINKER_FLAGS'] = '-framework AudioUnit'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.mpg123.de/download/mpg123-1.27.2.tar.bz2',
            '52f6ceb962c05db0c043bb27acf5a721381f5f356ac4610e5221f50293891b04',
            patches='mpg123-xcompile-fpu')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libmpg123.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.keep_module_target(state, 'MPG123::libmpg123')


class OggTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/xiph/ogg/releases/download/v1.3.5/libogg-1.3.5.tar.xz',
            'c4d91be36fc8e54deae7575241e03f4211eb102afb3fc0775fbbc1b740016705')

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
            'https://openal-soft.org/openal-releases/openal-soft-1.21.1.tar.bz2',
            'c8ad767e9a3230df66756a21cc8ebf218a9d47288f2514014832204e666af5d8')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'openal.pc.in')

    FRAMEWORKS = '-framework ApplicationServices -framework AudioToolbox -framework AudioUnit -framework CoreAudio'

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_cmake_libs(line: str):
            link_libs = '  INTERFACE_LINK_LIBRARIES '
            return f'{link_libs}"{OpenALTarget.FRAMEWORKS}"\n' if line.startswith(link_libs) else line

        config_path = state.install_path + '/lib/cmake/OpenAL/OpenALConfig.cmake'
        self.update_text_file(config_path, update_cmake_libs)

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        libs_private = 'Libs.private:'
        return f'{libs_private} {OpenALTarget.FRAMEWORKS}\n' if line.startswith(libs_private) else line


class OpusTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='opus'):
        super().__init__(name)
        self.options['PC_BUILD'] = 'floating-point'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.3.1.tar.gz',
            '65b58e1e25b2a114157014736a3d9dfeaad8d41be1c8179866f144a2fb44ff9d',
            patches='opus-fix-cmake')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'opus.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: str, line: str) -> str:
        version = 'Version:'
        cflags = 'Cflags:'
        libs = 'Libs:'

        if line.startswith(version):
            return version + ' 1.3.1\n'
        elif line.startswith(cflags):
            return cflags + ' -I${includedir}/opus\n'
        elif line.startswith(libs):
            return libs + ' -L${libdir} -lopus\n'

        return line


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


class SndFileTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sndfile'):
        super().__init__(name)

        opts = self.options
        opts['BUILD_REGTEST'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsndfile/releases/download/1.0.31/libsndfile-1.0.31.tar.bz2',
            'a8cfb1c09ea6e90eff4ca87322d4168cdbe5035cb48717b40bf77e751cc02163')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'sndfile.pc.in')


class VorbisTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/vorbis/libvorbis-1.3.7.tar.xz',
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
            'https://github.com/webmproject/libvpx/archive/v1.10.0.tar.gz',
            '85803ccbdbdd7a3b03d930187cb055f1353596969c1f92ebec2db839fa4f834a')

    def configure(self, state: BuildState):
        hosts = {
            'x86_64': 'x86_64-darwin13-gcc',
            'arm64': 'arm64-darwin20-gcc',
        }
        self.options['--target'] = hosts[state.architecture()]

        super().configure(state)

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'vpxstats.h')


class ZlibNgTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zlib-ng'):
        super().__init__(name)

        opts = self.options
        opts['ZLIB_COMPAT'] = 'YES'
        opts['ZLIB_ENABLE_TESTS'] = 'NO'
        opts['ZLIB_FULL_VERSION'] = '1.2.11'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/zlib-ng/zlib-ng/archive/refs/tags/2.0.3.tar.gz',
            '30305bd1551e3454bddf574f9863caf7137dde0fdbd4dcd7094eacfbb23955a0')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'zlib-ng.h')


class ZMusicTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zmusic'):
        super().__init__(name)

        opts = self.options
        opts['DYN_FLUIDSYNTH'] = 'OFF'
        opts['DYN_MPG123'] = 'OFF'
        opts['DYN_SNDFILE'] = 'OFF'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/coelckers/ZMusic/archive/refs/tags/1.1.8.tar.gz',
            '73082f661b7b0bb33348d1d186c132deec9132a1613480348a00172b49c9fd68')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/zmusic.h')
