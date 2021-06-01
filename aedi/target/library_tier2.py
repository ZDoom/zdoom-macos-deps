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

from .base import *
from ..state import BuildState


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


class FreeTypeTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='freetype'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/freetype/freetype2/2.10.4/freetype-2.10.4.tar.xz',
            '86a854d8905b19698bbc8f23b860bc104246ce4854dcea8e3b0fb21284f75784')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'include/freetype/freetype.h')


class MadTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='mad'):
        super().__init__(name)
        self.options['--enable-fpm'] = '64bit'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/mad/libmad/0.15.1b/libmad-0.15.1b.tar.gz',
            'bbfac3ed6bfbc2823d3775ebb931087371e142bb0e9bb1bee51a76a6e0078690',
            patches='mad-support-arm64')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'mad.h')

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


class OpusFileTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='opusfile'):
        super().__init__(name)
        self.options['--enable-http'] = 'no'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.osuosl.org/pub/xiph/releases/opus/opusfile-0.12.tar.gz',
            '118d8601c12dd6a44f52423e68ca9083cc9f2bfe72da7a8c1acb22a80ae3550b')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'opusfile.pc.in')


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
            '08e9a892bd80bdb1115213fb72dc29a7bf2ff108b378180586aa65f3cfd42e0f',
            patches='portmidi-modernize-cmake')

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
            'f6323b5e234753579d70a0af27796dde4ebeddf58aae4be598e39b3cee00c90a',
            patches='samplerate-support-arm64')

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
            'b4cf5a382c061cd75081cf246c2aa2f9df8db04bdda8dcdc6b6cca55bede2419',
            patches='sdl2_mixer-fix-fluidsynth')

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


class SodiumTarget(ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='sodium'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.libsodium.org/libsodium/releases/libsodium-1.0.18.tar.gz',
            '6f504490b342a4f8a4c4a02fc9b866cbef8622d5df4e5452b46be121e46636c1')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libsodium.pc.in')


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
