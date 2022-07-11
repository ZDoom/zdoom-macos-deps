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


class LzmaTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='lzma'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://tukaani.org/xz/xz-5.2.5.tar.gz',
            'f6f4910fd033078738bd82bfba4f49219d03b17eb0794eb91efbae419f4aba10',
            patches='lzma-add-cmake')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('src/liblzma/liblzma.pc.in')

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, 'liblzma.pc', name='liblzma',
                           description='General purpose data compression library',
                           version='5.2.5', libs='-llzma')


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
            'https://libsdl.org/release/SDL2-2.0.22.tar.gz',
            'fe7cbf3127882e3fc7259a75a0cb585620272c51745d3852ab9dd87960697f2e',
            patches=('sdl2-no-updaterev', 'sdl2-no-gamecontroller+corehaptic'))

    FRAMEWORKS = '-framework AudioToolbox -framework AVFoundation -framework Carbon' \
        ' -framework Cocoa -framework CoreAudio -framework CoreVideo -framework ForceFeedback' \
        ' -framework Foundation -framework IOKit -framework Metal -framework QuartzCore'
    LINKER_FLAGS = ' -L${libdir} -lSDL2 ' + FRAMEWORKS + os.linesep

    def configure(self, state: BuildState):
        state.options['SDL_STATIC_PIC'] = 'YES'
        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_sdl2_config(_: Path, line: str):
            if line.startswith('#    '):
                return None
            elif line.startswith('      echo -I'):
                return '      echo -I${prefix}/include/SDL2 -D_THREAD_SAFE\n'
            elif line.startswith('      echo -L'):
                return '      echo' + Sdl2Target.LINKER_FLAGS

            return line

        self.update_config_script(state.install_path / 'bin/sdl2-config', update_sdl2_config)

        def update_targets_cmake(line: str):
            libs = '  INTERFACE_LINK_LIBRARIES '
            return f'{libs}"{Sdl2Target.FRAMEWORKS}"\n' if line.startswith(libs) else line

        for suffix in ('', '-release'):
            file_path = state.install_path / f'lib/cmake/SDL2/SDL2staticTargets{suffix}.cmake'
            self.update_text_file(file_path, update_targets_cmake)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        libs = 'Libs:'

        if line.startswith(libs):
            return libs + Sdl2Target.LINKER_FLAGS

        return line


class Sdl2ImageTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_image'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsdl-org/SDL_image/releases/download/release-2.6.0/SDL2_image-2.6.0.tar.gz',
            '611c862f40de3b883393aabaa8d6df350aa3ae4814d65030972e402edae85aaa')

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, filename='SDL2_image.pc', name='SDL2_image',
                           description='image loading library for Simple DirectMedia Layer',
                           version='2.6.0', requires='sdl2 >= 2.0.9',
                           libs='-lSDL2_image', cflags='-I${includedir}/SDL2')

        bad_cmake_files_path = state.install_path / 'SDL2_image.framework/Resources'
        good_cmake_files_path = state.install_path / 'lib/cmake'

        if good_cmake_files_path.exists():
            shutil.rmtree(bad_cmake_files_path)

        shutil.move(str(bad_cmake_files_path), str(good_cmake_files_path))


class Sdl2MixerTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_mixer'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libsdl-org/SDL_mixer/releases/download/release-2.6.0/SDL2_mixer-2.6.0.tar.gz',
            'f94a4d3e878cb191c386a714be561838240012250fe17d496f4ff4341d59a391')

    def configure(self, state: BuildState):
        opts = state.options
        opts['SDL2MIXER_DEPS_SHARED'] = 'NO'
        opts['SDL2MIXER_MP3_MPG123'] = 'YES'
        opts['SDL2MIXER_OPUS_SHARED'] = 'NO'
        opts['SDL2MIXER_SAMPLES'] = 'NO'
        opts['SDL2MIXER_VORBIS'] = 'VORBISFILE'
        opts['SDL2MIXER_VORBIS_VORBISFILE_SHARED'] = 'NO'
        opts['SDL2MIXER_MOD_XMP'] = 'YES'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        self.write_pc_file(state, filename='SDL2_mixer.pc', name='SDL2_mixer',
                           description='mixer library for Simple DirectMedia Layer',
                           version='2.6.0', requires='sdl2 >= 2.0.9',
                           requires_private='flac fluidsynth libmodplug libmpg123 libxmp opusfile vorbisfile',
                           libs='-lSDL2_mixer', cflags='-I${includedir}/SDL2')


class Sdl2NetTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_net'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_net/release/SDL2_net-2.0.1.tar.gz',
            '15ce8a7e5a23dafe8177c8df6e6c79b6749a03fff1e8196742d3571657609d21')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('SDL2_net.pc.in')


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
            'https://github.com/KhronosGroup/Vulkan-Headers/archive/refs/tags/v1.3.216.tar.gz',
            '93f9a70ed9e956f3e0a1b41b71b6d030428cc3509e7e2b38d0ea6ba89b09f71e')


class VulkanLoaderTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='vulkan-loader'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            # Version should match with the current MoltenVK release
            'https://github.com/KhronosGroup/Vulkan-Loader/archive/refs/tags/v1.3.216.tar.gz',
            '006de2ee5bad4ef797ce4c25df166e09f2e5dd136e99cb507da313aa86770c00')

    def configure(self, state: BuildState):
        state.options['BUILD_STATIC_LOADER'] = 'YES'
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
