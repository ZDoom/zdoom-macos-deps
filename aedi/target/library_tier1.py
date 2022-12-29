#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020-2022 Alexey Lysiuk
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

from .base import *


class Bzip2Target(MakeTarget):
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


class FfiTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ffi'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libffi/libffi/releases/download/v3.4.2/libffi-3.4.2.tar.gz',
            '540fb721619a6aba3bdeef7d940d8e9e0e6d2c193595bc243241b77ff9e93620')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libffi.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)

        for header in ('ffi.h', 'ffitarget.h'):
            self.make_platform_header(state, header)


class FlacTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='flac'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/xiph/flac/releases/download/1.4.2/flac-1.4.2.tar.xz',
            'e322d58a1f48d23d9dd38f432672865f6f79e73a6f9cc5a5f57fcaa83eb5a8e4')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_CXXLIBS'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'

        super().configure(state)


class FluidSynthTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='fluidsynth'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v2.3.1.tar.gz',
            'd734e4cf488be763cf123e5976f3154f0094815093eecdf71e0e9ae148431883')

    def configure(self, state: BuildState):
        opts = state.options
        opts['DEFAULT_SOUNDFONT'] = 'default.sf2'
        opts['enable-framework'] = 'NO'
        opts['enable-readline'] = 'NO'
        opts['enable-sdl2'] = 'NO'

        super().configure(state)


class GettextTarget(ConfigureMakeStaticDependencyTarget):
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


class GlibTarget(BuildTarget):
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
        super().configure(state)

        environment = state.environment
        environment['LDFLAGS'] += ' -framework CoreFoundation -framework Foundation'

        c_compiler = state.c_compiler()
        assert c_compiler

        cxx_compiler = state.cxx_compiler()
        assert cxx_compiler

        cpu = state.architecture()
        cpu_family = 'arm' if 'arm64' == cpu else cpu

        cross_file = state.build_path / (state.architecture() + '.txt')
        with open(cross_file, 'w') as f:
            f.write(f'''
[binaries]
c = '{c_compiler}'
cpp = '{cxx_compiler}'
objc = '{c_compiler}'
objcpp = '{cxx_compiler}'
pkgconfig = '{state.prefix_path}/bin/pkg-config'
strip = '/usr/bin/strip'

[host_machine]
system = 'darwin'
cpu_family = '{cpu_family}'
cpu = '{cpu}'
endian = 'little'
''')

        args = (
            state.bin_path / 'meson',
            f'--prefix={state.install_path}',
            '--buildtype=release',
            '--default-library=static',
            f'--cross-file={cross_file}',
            state.source
        )
        subprocess.run(args, check=True, cwd=state.build_path, env=environment)

    def build(self, state: BuildState):
        args = ('ninja',)
        subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)

    def post_build(self, state: BuildState):
        self.install(state, tool='ninja')
        self.make_platform_header(state, '../lib/glib-2.0/include/glibconfig.h')

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        return 'exec_prefix=${prefix}\n' + line if line.startswith('libdir=') else line


class IconvTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='iconv'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/libiconv/libiconv-1.16.tar.gz',
            'e6a1b1b589654277ee790cce3734f07876ac4ccfaecbee8afa0b649cf529cc04')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('include/iconv.h.in')

    def configure(self, state: BuildState):
        state.options['--enable-extra-encodings'] = 'yes'
        super().configure(state)


class InstPatchTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='instpatch'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/swami/libinstpatch/archive/v1.1.6.tar.gz',
            '8e9861b04ede275d712242664dab6ffa9166c7940fea3b017638681d25e10299')

    def configure(self, state: BuildState):
        state.options['LIB_SUFFIX'] = None

        # Workaround for missing frameworks in dependencies, no clue what's wrong at the moment
        state.environment['LDFLAGS'] = '-framework CoreFoundation -framework Foundation'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        # Remove extra directory from include path
        include_path = state.install_path / 'include'
        include_subpath = include_path / 'libinstpatch-2/libinstpatch'
        shutil.move(str(include_subpath), include_path)


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


class JpegTurboTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='jpeg-turbo'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceforge.net/projects/libjpeg-turbo/files/2.1.4/libjpeg-turbo-2.1.4.tar.gz',
            'd3ed26a1131a13686dfca4935e520eb7c90ae76fbc45d98bb50a8dc86230342b')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ENABLE_SHARED'] = 'NO'
        opts['WITH_TURBOJPEG'] = 'NO'

        super().configure(state)


class LameTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='lame'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceforge.net/projects/lame/files/lame/3.100/lame-3.100.tar.gz',
            'ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('lame.spec')


class MoltenVKTarget(MakeTarget):
    def __init__(self, name='moltenvk'):
        super().__init__(name)

        # Building for multiple architectures is handled internally
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/MoltenVK/archive/refs/tags/v1.2.1.tar.gz',
            '4742df8f35473c5a737f2b120ae06aa6b9e8a7a3753b88932e501b06b1d17ea8',
            patches='moltenvk-deployment-target')

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
            src_path / 'MoltenVK.xcframework/macos-arm64_x86_64/libMoltenVK.a',
            lib_path / 'libMoltenVK-static.a')

        self._make_dylib(state)

    def _make_dylib(self, state: BuildState):
        lib_path = state.deps_path / self.name / 'lib'
        static_lib_path = lib_path / 'libMoltenVK-static.a'
        dynamic_lib_path = lib_path / 'libMoltenVK.dylib'

        static_lib_time = os.stat(static_lib_path).st_mtime
        dynamic_lib_time = os.stat(dynamic_lib_path).st_mtime if os.path.exists(dynamic_lib_path) else 0

        if static_lib_time != dynamic_lib_time:
            args = (
                'clang++',
                '-stdlib=libc++',
                '-dynamiclib',
                '-arch', 'arm64',
                '-arch', 'x86_64',
                '-mmacosx-version-min=10.12',
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
            )
            subprocess.run(args, check=True, env=state.environment)
            os.utime(dynamic_lib_path, (static_lib_time, static_lib_time))


class Mpg123Target(CMakeStaticDependencyTarget):
    def __init__(self, name='mpg123'):
        super().__init__(name)
        self.src_root = 'ports/cmake'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.mpg123.de/download/mpg123-1.31.1.tar.bz2',
            '5dcb0936efd44cb583498b6585845206f002a7b19d5066a2683be361954d955a',
            patches=('mpg123-arm64-fpu', 'mpg123-no-syn123'))

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_LIBOUT123'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'

        super().configure(state)


class OggTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='ogg'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/xiph/ogg/releases/download/v1.3.5/libogg-1.3.5.tar.xz',
            'c4d91be36fc8e54deae7575241e03f4211eb102afb3fc0775fbbc1b740016705')


class OpenALTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='openal'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://openal-soft.org/openal-releases/openal-soft-1.22.2.tar.bz2',
            'ae94cc95cda76b7cc6e92e38c2531af82148e76d3d88ce996e2928a1ea7c3d20')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ALSOFT_EXAMPLES'] = 'NO'
        opts['ALSOFT_UTILS'] = 'NO'
        opts['LIBTYPE'] = 'STATIC'

        super().configure(state)

    FRAMEWORKS = '-framework ApplicationServices -framework AudioToolbox -framework AudioUnit -framework CoreAudio'

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_cmake_libs(line: str):
            link_libs = '  INTERFACE_LINK_LIBRARIES '
            return f'{link_libs}"{OpenALTarget.FRAMEWORKS}"\n' if line.startswith(link_libs) else line

        config_path = state.install_path / 'lib/cmake/OpenAL/OpenALTargets.cmake'
        self.update_text_file(config_path, update_cmake_libs)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        libs_private = 'Libs.private:'
        return f'{libs_private} {OpenALTarget.FRAMEWORKS}\n' if line.startswith(libs_private) else line


class OpusTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='opus'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/opus/opus-1.3.1.tar.gz',
            '65b58e1e25b2a114157014736a3d9dfeaad8d41be1c8179866f144a2fb44ff9d',
            patches='opus-fix-cmake')

    def configure(self, state: BuildState):
        state.options['PC_BUILD'] = 'floating-point'
        super().configure(state)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
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


class QuasiGlibTarget(BuildTarget):
    def __init__(self, name='quasi-glib'):
        super().__init__(name)

    def build(self, state: BuildState):
        lib_path = state.install_path / 'lib'
        os.makedirs(lib_path, exist_ok=True)

        commands = (
            (state.cxx_compiler(), '-std=c++11', '-O3', '-c', state.patch_path / f'{self.name}.cpp'),
            (state.host() + '-ar', '-crs', lib_path / f'lib{self.name}.a', f'{self.name}.o'),
        )

        for command in commands:
            subprocess.run(command, check=True, cwd=state.build_path, env=state.environment)


class SndFileTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sndfile'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsndfile/releases/download/1.2.0/libsndfile-1.2.0.tar.xz',
            '0e30e7072f83dc84863e2e55f299175c7e04a5902ae79cfb99d4249ee8f6d60a')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_EXAMPLES'] = 'NO'
        opts['BUILD_PROGRAMS'] = 'NO'
        opts['BUILD_TESTING'] = 'NO'
        opts['ENABLE_CPACK'] = 'NO'

        super().configure(state)


class VorbisTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='vorbis'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/vorbis/libvorbis-1.3.7.tar.xz',
            'b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b')


class VpxTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='vpx'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/webmproject/libvpx/archive/refs/tags/v1.12.0.tar.gz',
            'f1acc15d0fd0cb431f4bf6eac32d5e932e40ea1186fe78e074254d6d003957bb')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('vpxstats.h')

    def configure(self, state: BuildState):
        hosts = {
            'x86_64': 'x86_64-darwin16-gcc',
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


class ZlibNgTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zlib-ng'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/zlib-ng/zlib-ng/archive/refs/tags/2.0.6.tar.gz',
            '8258b75a72303b661a238047cb348203d88d9dddf85d480ed885f375916fcab6')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('zlib-ng.h')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ZLIB_COMPAT'] = 'YES'
        opts['ZLIB_ENABLE_TESTS'] = 'NO'
        opts['ZLIB_FULL_VERSION'] = '1.2.11'

        super().configure(state)


class ZMusicTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='zmusic'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ZDoom/ZMusic/archive/refs/tags/1.1.11.tar.gz',
            '623c3d7edfcdbe1ba4e7a9dc9a4d834fb92a228881621247855ecd57447631dd')

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
