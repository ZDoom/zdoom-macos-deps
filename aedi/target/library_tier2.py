#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020-2023 Alexey Lysiuk
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


class DumbTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='dumb'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/kode54/dumb/archive/2.0.3.tar.gz',
            '99bfac926aeb8d476562303312d9f47fd05b43803050cd889b44da34a9b2a4f9')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('include/dumb.h')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_ALLEGRO4'] = 'NO'
        opts['BUILD_EXAMPLES'] = 'NO'

        super().configure(state)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        return 'Libs: -L${libdir} -ldumb\n' if line.startswith('Libs:') else line


class FmtTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='fmt'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/fmtlib/fmt/archive/refs/tags/8.1.1.tar.gz',
            '3d794d3cf67633b34b2771eb9f073bde87e846e0d395d254df7b211ef1ec7346')

    def configure(self, state: BuildState):
        opts = state.options
        opts['FMT_DOC'] = 'NO'
        opts['FMT_TEST'] = 'NO'

        super().configure(state)


class MadTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mad'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/mad/libmad/0.15.1b/libmad-0.15.1b.tar.gz',
            'bbfac3ed6bfbc2823d3775ebb931087371e142bb0e9bb1bee51a76a6e0078690',
            patches='mad-support-arm64')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('mad.h')

    def configure(self, state: BuildState):
        state.options['--enable-fpm'] = '64bit'
        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.write_pc_file(state, description='MPEG Audio Decoder', version='0.15.1b')


class MikmodTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mikmod'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/mikmod/libmikmod/3.3.11.1/libmikmod-3.3.11.1.tar.gz',
            'ad9d64dfc8f83684876419ea7cd4ff4a41d8bcd8c23ef37ecb3a200a16b46d19')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libmikmod.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)
        self.update_config_script(state.install_path / 'bin/libmikmod-config')


class ModPlugTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='modplug'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/modplug-xmms/libmodplug/0.8.9.0/libmodplug-0.8.9.0.tar.gz',
            '457ca5a6c179656d66c01505c0d95fafaead4329b9dbaa0f997d00a3508ad9de')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libmodplug.pc.in')

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        libs_private = 'Libs.private:'

        if line.startswith(libs_private):
            return libs_private + ' -lc++\n'

        return line


class OpusFileTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opusfile'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/opus/opusfile-0.12.tar.gz',
            '118d8601c12dd6a44f52423e68ca9083cc9f2bfe72da7a8c1acb22a80ae3550b')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('opusfile.pc.in')

    def configure(self, state: BuildState):
        state.options['--enable-http'] = 'no'
        super().configure(state)


class PngTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='png'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/libpng/libpng-1.6.37.tar.xz',
            '505e70834d35383537b6491e7ae8641f1a4bed1876dbfe361201fc80868d88ca')

    def configure(self, state: BuildState):
        opts = state.options
        opts['PNG_ARM_NEON'] = 'on'
        opts['PNG_SHARED'] = 'OFF'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_cmake_libs(line: str):
            link_libs = '  INTERFACE_LINK_LIBRARIES '
            return f'{link_libs}"ZLIB::ZLIB"\n' if line.startswith(link_libs) else line

        self.update_text_file(state.install_path / 'lib/libpng/libpng16.cmake', update_cmake_libs)
        self.update_config_script(state.install_path / 'bin/libpng16-config')


class PortMidiTarget(CMakeTarget):
    def __init__(self, name='portmidi'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/portmedia/portmidi/217/portmidi-src-217.zip',
            '08e9a892bd80bdb1115213fb72dc29a7bf2ff108b378180586aa65f3cfd42e0f',
            patches='portmidi-modernize-cmake')

    def post_build(self, state: BuildState):
        if state.install_path.exists():
            shutil.rmtree(state.install_path)

        include_path = state.install_path / 'include'
        os.makedirs(include_path)
        shutil.copy(state.source / 'pm_common/portmidi.h', include_path)
        shutil.copy(state.source / 'porttime/porttime.h', include_path)

        lib_path = state.install_path / 'lib'
        os.makedirs(lib_path)
        shutil.copy(state.build_path / 'libportmidi_s.a', lib_path / 'libportmidi.a')


class SamplerateTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='samplerate'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsndfile/libsamplerate/releases/download/0.2.1/libsamplerate-0.2.1.tar.bz2',
            'f6323b5e234753579d70a0af27796dde4ebeddf58aae4be598e39b3cee00c90a')

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_linker_flags(line: str):
            link_var = '  INTERFACE_LINK_LIBRARIES '
            return None if line.startswith(link_var) else line

        cmake_module = state.install_path / 'lib/cmake/SampleRate/SampleRateTargets.cmake'
        self.update_text_file(cmake_module, update_linker_flags)


class Sdl2Target(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsdl-org/SDL/releases/download/release-2.26.2/SDL2-2.26.2.tar.gz',
            '95d39bc3de037fbdfa722623737340648de4f180a601b0afad27645d150b99e0',
            patches='sdl2-no-gamecontroller+corehaptic')

    def configure(self, state: BuildState):
        opts = state.options
        opts['SDL_STATIC_PIC'] = 'YES'
        opts['SDL_TEST'] = 'NO'

        super().configure(state)


class Sdl2ImageTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_image'):
        super().__init__(name)
        self.version = '2.6.2'

    def prepare_source(self, state: BuildState):
        base_url = 'https://github.com/libsdl-org/SDL_image/releases/download'
        state.download_source(
            f'{base_url}/release-{self.version}/SDL2_image-{self.version}.tar.gz',
            '48355fb4d8d00bac639cd1c4f4a7661c4afef2c212af60b340e06b7059814777')

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, filename='SDL2_image.pc', name='SDL2_image',
                           description='image loading library for Simple DirectMedia Layer',
                           version=self.version, requires='sdl2 >= 2.0.9',
                           libs='-lSDL2_image', cflags='-I${includedir}/SDL2')

        bad_cmake_files_path = state.install_path / 'SDL2_image.framework/Resources'
        good_cmake_files_path = state.install_path / 'lib/cmake'

        if good_cmake_files_path.exists():
            shutil.rmtree(bad_cmake_files_path)

        shutil.move(str(bad_cmake_files_path), str(good_cmake_files_path))


class Sdl2MixerTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_mixer'):
        super().__init__(name)
        self.version = '2.6.2'

    def prepare_source(self, state: BuildState):
        base_url = 'https://github.com/libsdl-org/SDL_mixer/releases/download'
        state.download_source(
            f'{base_url}/release-{self.version}/SDL2_mixer-{self.version}.tar.gz',
            '8cdea810366decba3c33d32b8071bccd1c309b2499a54946d92b48e6922aa371')

    def configure(self, state: BuildState):
        opts = state.options
        opts['SDL2MIXER_DEPS_SHARED'] = 'NO'
        opts['SDL2MIXER_MOD_XMP'] = 'YES'
        opts['SDL2MIXER_MP3_MPG123'] = 'YES'
        opts['SDL2MIXER_OPUS_SHARED'] = 'NO'
        opts['SDL2MIXER_SAMPLES'] = 'NO'
        opts['SDL2MIXER_VORBIS'] = 'VORBISFILE'
        opts['SDL2MIXER_VORBIS_VORBISFILE_SHARED'] = 'NO'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, filename='SDL2_mixer.pc', name='SDL2_mixer',
                           description='mixer library for Simple DirectMedia Layer',
                           version=self.version, requires='sdl2 >= 2.0.9',
                           requires_private='flac fluidsynth libmodplug libmpg123 libxmp opusfile vorbisfile',
                           libs='-lSDL2_mixer', cflags='-I${includedir}/SDL2')


class Sdl2NetTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_net'):
        super().__init__(name)
        self.version = '2.2.0'

    def prepare_source(self, state: BuildState):
        base_url = 'https://github.com/libsdl-org/SDL_net/releases'
        state.download_source(
            f'{base_url}/release-{self.version}/SDL2_net-{self.version}.tar.gz',
            '4e4a891988316271974ff4e9585ed1ef729a123d22c08bd473129179dc857feb')

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, filename='SDL2_net.pc', name='SDL2_net',
                           description='net library for Simple DirectMedia Layer',
                           version=self.version, requires='sdl2 >= 2.0.4',
                           libs='-lSDL2_net', cflags='-I${includedir}/SDL2')


class SodiumTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sodium'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.libsodium.org/libsodium/releases/libsodium-1.0.18.tar.gz',
            '6f504490b342a4f8a4c4a02fc9b866cbef8622d5df4e5452b46be121e46636c1')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libsodium.pc.in')


class VulkanHeadersTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='vulkan-headers'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            # Version should match with the current MoltenVK release
            'https://github.com/KhronosGroup/Vulkan-Headers/archive/refs/tags/v1.3.239.tar.gz',
            '86ef8969b96cf391dc86b9c4e5745b8ecaa12ebdaaefd3d8e38bc98e15f30653')


class VulkanLoaderTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='vulkan-loader'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            # Version should match with the current MoltenVK release
            'https://github.com/KhronosGroup/Vulkan-Loader/archive/refs/tags/v1.3.236.tar.gz',
            'c18434976d6e67c3c1d5cfdfa630046e698402d1f666ff5094de1fcd3a012b0d')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_STATIC_LOADER'] = 'YES'
        opts['CMAKE_INSTALL_SYSCONFDIR'] = '/usr/local/etc'

        super().configure(state)


class XmpTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='xmp'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://sourceforge.net/projects/xmp/files/libxmp/4.5.0/libxmp-4.5.0.tar.gz',
            '7847d262112d14e8442f44e5ac6ed9ddbca54c251284720b563c852b31f26e75')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libxmp.pc.in')

    def configure(self, state: BuildState):
        state.options['--enable-static'] = None
        super().configure(state)
