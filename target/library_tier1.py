#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020-2025 Alexey Lysiuk
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
import shlex
import shutil
import subprocess
from pathlib import Path

import aedi.target.base as base
from aedi.state import BuildState


class Bzip2Target(base.MakeTarget):
    def __init__(self, name='bzip2'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz',
            'ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('bzlib.h')

    def configure(self, state: BuildState):
        super().configure(state)

        opts = state.options
        # Add explicit targets in order to skip testing step that is incompatible with cross-compilation
        opts['bzip2'] = None
        opts['bzip2recover'] = None
        # Copy compiler flags from environment to command line argument, they would be overridden by Makefile otherwise
        cflags = 'CFLAGS'
        opts[cflags] = state.environment[cflags] + ' -D_FILE_OFFSET_BITS=64 -O2'

    def post_build(self, state: BuildState):
        opts = state.options
        opts['install'] = None
        opts['PREFIX'] = state.install_path

        self.install(state, state.options)
        self.write_pc_file(state, description='bzip2 compression library', version='1.0.8', libs='-lbz2')


class FfiTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ffi'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libffi/libffi/releases/download/v3.4.6/libffi-3.4.6.tar.gz',
            'b0dea9df23c863a7a50e825440f3ebffabd65df1497108e5d437747843895a4e')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libffi.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)

        for header in ('ffi.h', 'ffitarget.h'):
            self.make_platform_header(state, header)


class FlacTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='flac'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/xiph/flac/releases/download/1.5.0/flac-1.5.0.tar.xz',
            'f2c1c76592a82ffff8413ba3c4a1299b6c7ab06c734dee03fd88630485c2b920')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_CXXLIBS'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'

        super().configure(state)


class GettextTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='gettext'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/gettext/gettext-0.21.tar.xz',
            'd20fcbb537e02dcf1383197ba05bd0734ef7bf5db06bdb241eb69b7d16b73192')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('gettext-runtime')

    def configure(self, state: BuildState):
        opts = state.options
        opts['--enable-csharp'] = 'no'
        opts['--enable-java'] = 'no'
        opts['--enable-libasprintf'] = 'no'

        super().configure(state)


class GlibTarget(base.MesonTarget):
    def __init__(self, name='glib'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.gnome.org/sources/glib/2.72/glib-2.72.3.tar.xz',
            '4a39a2f624b8512d500d5840173eda7fa85f51c109052eae806acece85d345f0',
            patches='glib-fix-paths')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('glib.doap')

    def configure(self, state: BuildState):
        # Additional frameworks are needed for proper detection of libintl
        ld_key = 'LDFLAGS'
        ld_value = '-framework CoreFoundation -framework Foundation'
        env = state.environment
        env[ld_key] = (env[ld_key] + ' ' + ld_value) if ld_key in env else ld_value

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.make_platform_header(state, '../lib/glib-2.0/include/glibconfig.h')

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        return 'exec_prefix=${prefix}\n' + line if line.startswith('libdir=') else line


class IconvTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='iconv'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/libiconv/libiconv-1.17.tar.gz',
            '8f74213b56238c85a50a5329f77e06198771e70dd9a739779f4c02f65d971313')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('include/iconv.h.in')

    def configure(self, state: BuildState):
        state.options['--enable-extra-encodings'] = 'yes'
        super().configure(state)


class IntlTarget(GettextTarget):
    def __init__(self, name='intl'):
        super().__init__(name)

    def configure(self, state: BuildState):
        state.options['--localedir'] = '/usr/local/share/locale'

        # There is no way to configure intl only, do this for the runtime
        self.src_root = 'gettext-runtime'
        super().configure(state)

    def build(self, state: BuildState):
        # Build intl only, avoid complete gettext runtime
        self.src_root += '/intl'
        super().build(state)

    def post_build(self, state: BuildState):
        opts = state.options
        opts['install-exec-am'] = None
        opts['install-nodist_includeHEADERS'] = None

        # Install intl only, avoid complete gettext runtime
        state.build_path /= self.src_root
        self.install(state, state.options)


class LameTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='lame'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceforge.net/projects/lame/files/lame/3.100/lame-3.100.tar.gz',
            'ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('lame.spec')


class MoltenVKTarget(base.MakeTarget):
    def __init__(self, name='moltenvk'):
        super().__init__(name)

        # Building for multiple architectures is handled internally
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/MoltenVK/archive/refs/tags/v1.2.11.tar.gz',
            'bfa115e283831e52d70ee5e13adf4d152de8f0045996cf2a33f0ac541be238b1')

    def initialize(self, state: BuildState):
        super().initialize(state)
        self._make_dylib(state)

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('MoltenVKPackaging.xcodeproj')

    def configure(self, state: BuildState):
        state.options['macos'] = None

        # Unset platform to avoid using specified macOS deployment target and SDK
        # MoltenVK defines minimal OS version itself, and usually, it requires the very recent SDK
        state.platform = None

        super().configure(state)

    def build(self, state: BuildState):
        args = ['./fetchDependencies', '--macos']
        if state.verbose:
            args.append('-v')
        subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)

        super().build(state)

    def post_build(self, state: BuildState):
        if state.xcode:
            return

        if state.install_path.exists():
            shutil.rmtree(state.install_path)

        include_path = state.install_path / 'include'
        os.makedirs(include_path)

        lib_path = state.install_path / 'lib'
        os.makedirs(lib_path)

        src_path = state.build_path / 'Package/Latest/MoltenVK'
        shutil.copytree(src_path / 'include/MoltenVK', include_path / 'MoltenVK')
        shutil.copy(state.build_path / 'LICENSE', state.install_path / 'apache2.txt')
        shutil.copy(
            src_path / 'static/MoltenVK.xcframework/macos-arm64_x86_64/libMoltenVK.a',
            lib_path / 'libMoltenVK-static.a')

        self._make_dylib(state)

    def _make_dylib(self, state: BuildState):
        lib_path = state.deps_path / self.name / 'lib'
        static_lib_path = lib_path / 'libMoltenVK-static.a'
        dynamic_lib_path = lib_path / 'libMoltenVK.dylib'

        static_lib_time = os.stat(static_lib_path).st_mtime
        dynamic_lib_time = os.stat(dynamic_lib_path).st_mtime if os.path.exists(dynamic_lib_path) else 0

        if static_lib_time != dynamic_lib_time:
            os.makedirs(state.lib_path, exist_ok=True)

            args = [
                'clang++',
                '-stdlib=libc++',
                '-dynamiclib',
                '-arch', 'arm64',
                '-arch', 'x86_64',
                '-mmacosx-version-min=10.15',
                '-compatibility_version', '1.0.0',
                '-current_version', '1.0.0',
                '-install_name', '@rpath/libMoltenVK.dylib',
                '-framework', 'Metal',
                '-framework', 'IOSurface',
                '-framework', 'AppKit',
                '-framework', 'QuartzCore',
                '-framework', 'CoreGraphics',
                '-framework', 'IOKit',
                '-framework', 'Foundation',
                '-o', dynamic_lib_path,
                '-force_load', static_lib_path
            ]
            args += shlex.split(state.linker_flags())

            subprocess.run(args, check=True, env=state.environment)
            os.utime(dynamic_lib_path, (static_lib_time, static_lib_time))


class Mpg123Target(base.CMakeStaticDependencyTarget):
    def __init__(self, name='mpg123'):
        super().__init__(name)
        self.src_root = 'ports/cmake'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.mpg123.de/download/mpg123-1.32.10.tar.bz2',
            '87b2c17fe0c979d3ef38eeceff6362b35b28ac8589fbf1854b5be75c9ab6557c',
            patches=('mpg123-have-fpu', 'mpg123-no-syn123'))

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_LIBOUT123'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'

        super().configure(state)


class OggTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/xiph/ogg/releases/download/v1.3.5/libogg-1.3.5.tar.xz',
            'c4d91be36fc8e54deae7575241e03f4211eb102afb3fc0775fbbc1b740016705')


class OpenALTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='openal'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://openal-soft.org/openal-releases/openal-soft-1.24.3.tar.bz2',
            'cb5e6197a1c0da0edcf2a81024953cc8fa8545c3b9474e48c852af709d587892')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ALSOFT_EXAMPLES'] = 'NO'
        opts['ALSOFT_UTILS'] = 'NO'
        opts['LIBTYPE'] = 'STATIC'

        super().configure(state)


class OpusTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='opus'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        # Temporary solution for lack of TLSv1.3 support in Apple Python
        # The following URL cannot be retrieved using Python 3.9.6 from Xcode 15.x
        # https://downloads.xiph.org/releases/opus/opus-1.5.1.tar.gz
        # ssl.SSLError: [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl.c:1129)
        # >>> import ssl; print(ssl.OPENSSL_VERSION, ssl.HAS_TLSv1_3)
        # LibreSSL 2.8.3 False
        # TODO: remove this workaround when TLSv1.3 will be available in Python shipped with Xcode
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.5.2.tar.gz',
            '65c1d2f78b9f2fb20082c38cbe47c951ad5839345876e46941612ee87f9a7ce1')

    def configure(self, state: BuildState):
        state.options['PC_BUILD'] = 'floating-point'
        super().configure(state)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        cflags = 'Cflags:'
        libs = 'Libs:'

        if line.startswith(cflags):
            return cflags + ' -I${includedir}/opus\n'
        elif line.startswith(libs):
            return libs + ' -L${libdir} -lopus\n'

        return line


class PcreTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='pcre'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.pcre.org/pub/pcre/pcre-8.45.tar.bz2',
            '4dae6fdcd2bb0bb6c37b5f97c33c2be954da743985369cddac3546e3218bffb8')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('pcre.h.in')

    def configure(self, state: BuildState):
        opts = state.options
        opts['--enable-unicode-properties'] = 'yes'
        opts['--enable-cpp'] = 'no'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.update_config_script(state.install_path / 'bin/pcre-config')


class QuasiGlibTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='quasi-glib'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.source = state.patch_path / self.name


class SndFileTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='sndfile'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsndfile/releases/download/1.2.2/libsndfile-1.2.2.tar.xz',
            '3799ca9924d3125038880367bf1468e53a1b7e3686a934f098b7e1d286cdb80e')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_EXAMPLES'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'
        opts['ENABLE_CPACK'] = 'NO'

        super().configure(state)


class VorbisTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/vorbis/libvorbis-1.3.7.tar.xz',
            'b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b')


class VpxTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='vpx'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/webmproject/libvpx/archive/refs/tags/v1.15.0.tar.gz',
            'e935eded7d81631a538bfae703fd1e293aad1c7fd3407ba00440c95105d2011e')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('vpxstats.h')

    def configure(self, state: BuildState):
        hosts = {
            'x86_64': 'x86_64-darwin19-gcc',
            'arm64': 'arm64-darwin20-gcc',
        }

        opts = state.options
        opts['--disable-examples'] = None
        opts['--disable-unit-tests'] = None
        opts['--target'] = hosts[state.architecture()]

        super().configure(state)

        def clean_build_config(line: str):
            cfg_prefix = 'static const char* const cfg = '
            return f'{cfg_prefix}"";\n' if line.startswith(cfg_prefix) else line

        self.update_text_file(state.build_path / 'vpx_config.c', clean_build_config)


class ZMusicTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='zmusic'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ZDoom/ZMusic/archive/refs/tags/1.1.14.tar.gz',
            'f04410fe4ea08136f37703e7715c27df4c8532ace1e721cf40c6f303a93acc54')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('include/zmusic.h')

    def configure(self, state: BuildState):
        opts = state.options
        opts['DYN_MPG123'] = 'OFF'
        opts['DYN_SNDFILE'] = 'OFF'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        # Fix full path to glib
        link_libs_key = '  INTERFACE_LINK_LIBRARIES '
        link_libs_value = r'"\$<LINK_ONLY:sndfile>;\$<LINK_ONLY:mpg123>;\$<LINK_ONLY:ZLIB::ZLIB>;glib-2.0"'
        module_path = state.install_path / 'lib/cmake/ZMusic'

        def update_cmake_libs(line: str):
            return f'{link_libs_key}{link_libs_value}\n' if line.startswith(link_libs_key) else line

        for kind in ('Full', 'Lite'):
            self.update_text_file(module_path / f'ZMusic{kind}Targets.cmake', update_cmake_libs)
