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

import os
import shutil
from pathlib import Path
from platform import machine

from ..state import BuildState
from .base import CMakeTarget, MakeTarget


class MakeMainTarget(MakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

        self.destination = self.DESTINATION_OUTPUT


class CMakeMainTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

        self.destination = self.DESTINATION_OUTPUT
        self.outputs = (self.name + '.app',)

    def post_build(self, state: BuildState):
        if state.xcode:
            return

        if state.install_path.exists():
            shutil.rmtree(state.install_path)

        os.makedirs(state.install_path)

        for output in self.outputs:
            src = state.build_path / output
            dst_sep_pos = output.rfind(os.sep)
            dst = state.install_path / (output if dst_sep_pos == -1 else output[dst_sep_pos + 1:])

            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)

    @staticmethod
    def _force_cross_compilation(state: BuildState):
        if state.architecture() == machine():
            return

        opts = state.options
        opts['FORCE_CROSSCOMPILE'] = 'YES'
        opts['IMPORT_EXECUTABLES'] = state.native_build_path / 'ImportExecutables.cmake'

    @staticmethod
    def _force_openal_soft(state: BuildState):
        # Explicit OpenAL configuration to avoid selection of Apple's framework
        opts = state.options
        opts['OPENAL_INCLUDE_DIR'] = state.include_path / 'AL'
        opts['OPENAL_LIBRARY'] = state.lib_path / 'libopenal.a'


class CMakeSingleExeMainTarget(CMakeMainTarget):
    def __init__(self, name=None):
        super().__init__(name)
        self.outputs = (name,)


class ZDoomBaseTarget(CMakeMainTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        pkg_config_args = ['--libs', 'openal', 'sndfile']
        linker_flags = ''

        if state.quasi_glib:
            linker_flags = '-lquasi-glib '
        else:
            pkg_config_args.append('glib-2.0')

        opts = state.options
        opts['CMAKE_EXE_LINKER_FLAGS'] += linker_flags + state.run_pkg_config(*pkg_config_args)
        opts['PK3_QUIET_ZIPDIR'] = 'YES'
        opts['DYN_OPENAL'] = 'NO'

        self._force_cross_compilation(state)
        self._force_openal_soft(state)

        super().configure(state)


class ZDoomVulkanBaseTarget(ZDoomBaseTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        if state.static_moltenvk:
            state.options['CMAKE_EXE_LINKER_FLAGS'] += '-framework Metal -framework IOSurface -lMoltenVK-static'

            # Unset SDK because MoltenVK usually requires the latest one shipped with Xcode
            state.platform.sdk_path = None

            # Replace volk and update revision files
            replacement_src_path = state.patch_path / 'static-moltenvk'
            replacement_files = ('UpdateRevision.cmake', 'volk.c', 'volk.h')

            # TODO: remove old code path when ZVulkan is merged into Raze
            zvulkan_base_path = Path('libraries/ZVulkan')
            has_zvulkan = os.path.exists(state.source / zvulkan_base_path)
            replacement_dst_volk_path = None

            if has_zvulkan:
                volk_h_dst_path = state.source / zvulkan_base_path / 'src/volk/volk.h'

                if not os.path.exists(volk_h_dst_path):
                    os.symlink(replacement_src_path / 'volk.h', volk_h_dst_path)
            else:
                replacement_dst_volk_subpath = 'common/rendering/vulkan/thirdparty/volk/'
                replacement_dst_volk_path = Path('src') / replacement_dst_volk_subpath  # GZDoom path

                if not os.path.exists(state.source / replacement_dst_volk_path):
                    replacement_dst_volk_path = Path('source') / replacement_dst_volk_subpath  # Raze path

            replacement_dst_paths = (
                'tools/updaterevision',
                zvulkan_base_path / 'src/volk' if has_zvulkan else replacement_dst_volk_path,  # volk.c
                zvulkan_base_path / 'include/zvulkan/volk' if has_zvulkan else replacement_dst_volk_path  # volk.h
            )

            for dst_path, filename in zip(replacement_dst_paths, replacement_files):
                src = replacement_src_path / filename
                dst = state.source / dst_path / filename

                src_stat = os.stat(src)
                dst_stat = os.stat(dst)

                if src_stat.st_size != dst_stat.st_size or src_stat.st_mtime != dst_stat.st_mtime:
                    shutil.copy2(src, dst)

        super().configure(state)

    def post_build(self, state: BuildState):
        if not state.static_moltenvk:
            # Put MoltenVK library into application bundle
            molten_lib = 'libMoltenVK.dylib'
            src_path = state.lib_path / molten_lib
            dst_path = state.build_path

            if state.xcode:
                # TODO: Support other configurations
                dst_path /= 'Debug'

            dst_path /= self.name + '.app/Contents/MacOS'
            os.makedirs(dst_path, exist_ok=True)

            dst_path /= molten_lib

            if not dst_path.exists():
                copy_func = state.xcode and os.symlink or shutil.copy
                copy_func(src_path, dst_path)

        super().post_build(state)


class GZDoomTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='gzdoom'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/gzdoom.git')


class QZDoomTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='qzdoom'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/qzdoom.git')


class LZDoomTarget(ZDoomBaseTarget):
    def __init__(self, name='lzdoom'):
        super().__init__(name)
        self.unsupported_architectures = ('arm64',)

    def configure(self, state: BuildState):
        opts = state.options
        opts['DYN_FLUIDSYNTH'] = 'NO'
        opts['DYN_MPG123'] = 'NO'
        opts['DYN_SNDFILE'] = 'NO'

        super().configure(state)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/drfrag666/gzdoom.git', branch='g3.3mgw')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('ico_lzdoom.png')


class RazeTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='raze'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/Raze.git')


class HandsOfNecromancyTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='handsofnecromancy'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/HandsOfNecromancy/HandsOfNecromancy-Engine.git')


class RedemptionTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='redemption'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/RedemptionEngine/redemption.git')


class DisdainTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='disdain'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/MischiefDonut/disdain-src.git')


class AccTarget(CMakeSingleExeMainTarget):
    def __init__(self, name='acc'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/acc.git')


class WadExtTarget(CMakeSingleExeMainTarget):
    def __init__(self, name='wadext'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/wadext.git')


class ZdbspTarget(CMakeSingleExeMainTarget):
    def __init__(self, name='zdbsp'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/zdbsp.git')


class ZDRayTarget(CMakeSingleExeMainTarget):
    def __init__(self, name='zdray'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/ZDoom/ZDRay.git')


class PrBoomPlusTarget(CMakeMainTarget):
    def __init__(self, name='prboom-plus'):
        super().__init__(name)
        self.src_root = 'prboom2'
        self.outputs = ('Launcher.app',)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/coelckers/prboom-plus.git')

    def configure(self, state: BuildState):
        opts = state.options
        opts['CMAKE_C_FLAGS'] = '-D_FILE_OFFSET_BITS=64'
        opts['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'SDL2_mixer', 'SDL2_image')
        opts['CMAKE_POLICY_DEFAULT_CMP0056'] = 'NEW'

        self._force_cross_compilation(state)

        super().configure(state)


class DsdaDoom(PrBoomPlusTarget):
    def __init__(self, name='dsda-doom'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/kraflab/dsda-doom.git')


class ChocolateDoomBaseTarget(CMakeMainTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        state.options['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'SDL2_mixer')
        super().configure(state)

    def _fill_outputs(self, exe_prefix: str):
        self.outputs = (
            f'src/{exe_prefix}-doom',
            f'src/{exe_prefix}-heretic',
            f'src/{exe_prefix}-hexen',
            f'src/{exe_prefix}-server',
            f'src/{exe_prefix}-setup',
            f'src/{exe_prefix}-strife',
            'src/midiread',
            'src/mus2mid',
        )


class ChocolateDoomTarget(ChocolateDoomBaseTarget):
    def __init__(self, name='chocolate-doom'):
        super().__init__(name)
        self._fill_outputs('chocolate')

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/chocolate-doom/chocolate-doom.git')


class CrispyDoomTarget(ChocolateDoomBaseTarget):
    def __init__(self, name='crispy-doom'):
        super().__init__(name)
        self._fill_outputs('crispy')

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/fabiangreffrath/crispy-doom.git')


class RudeTarget(ChocolateDoomBaseTarget):
    def __init__(self, name='rude'):
        super().__init__(name)
        self._fill_outputs('rude')

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/drfrag666/RUDE.git')

    def post_build(self, state: BuildState):
        super().post_build(state)
        shutil.copy(state.source + '/data/rude.wad', state.install_path)


class WoofTarget(ChocolateDoomBaseTarget):
    def __init__(self, name='woof'):
        super().__init__(name)
        self.outputs = ('Source/woof',)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/fabiangreffrath/woof.git')


class DoomRetroTarget(CMakeMainTarget):
    def __init__(self, name='doomretro'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/bradharding/doomretro.git')


class Doom64EXTarget(CMakeMainTarget):
    def __init__(self, name='doom64ex'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/svkaiser/Doom64EX.git')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ENABLE_SYSTEM_FLUIDSYNTH'] = 'YES'
        opts['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'SDL2', 'fluidsynth')

        super().configure(state)


class DevilutionXTarget(CMakeMainTarget):
    def __init__(self, name='devilutionx'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/diasurgical/devilutionX.git')

    def configure(self, state: BuildState):
        state.options['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'SDL2_mixer', 'SDL2_ttf')
        super().configure(state)

        # Remove version file that is included erroneously because of case-insensitive file system
        version_file = state.build_path / '_deps/libzt-src/ext/ZeroTierOne/ext/miniupnpc/VERSION'
        version_file.unlink(missing_ok=True)


class EDuke32Target(MakeMainTarget):
    def __init__(self, name='eduke32'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://voidpoint.io/terminx/eduke32.git')

    def detect(self, state: BuildState) -> bool:
        def has_bundle(name: str) -> bool:
            probe_path = state.source / f'platform/Apple/bundles/{name}.app'
            return probe_path.exists()

        return has_bundle('EDuke32') and not has_bundle('NBlood')


class NBloodTarget(EDuke32Target):
    def __init__(self, name='nblood'):
        super().__init__(name)
        self.tool = 'gmake'

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/nukeykt/NBlood.git')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('nblood.pk3')

    def configure(self, state: BuildState):
        super().configure(state)

        for target in ('duke3d', 'sw', 'blood', 'rr', 'exhumed', 'tools'):
            state.options[target] = None


class QuakespasmTarget(MakeMainTarget):
    def __init__(self, name='quakespasm'):
        super().__init__(name)
        self.src_root = 'Quake'

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://git.code.sf.net/p/quakespasm/quakespasm')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('Quakespasm.txt') and not QuakespasmExpTarget().detect(state)

    def configure(self, state: BuildState):
        super().configure(state)

        # TODO: Use macOS specific Makefile which requires manual application bundle creation
        opts = state.options
        opts['USE_SDL2'] = '1'
        opts['USE_CODEC_FLAC'] = '1'
        opts['USE_CODEC_OPUS'] = '1'
        opts['USE_CODEC_MIKMOD'] = '1'
        opts['USE_CODEC_UMX'] = '1'
        # Add main() alias to workaround executable linking without macOS launcher
        opts['COMMON_LIBS'] = '-framework OpenGL -Wl,-alias -Wl,_SDL_main -Wl,_main'


class QuakespasmExpTarget(CMakeMainTarget):
    def __init__(self, name='quakespasm-exp'):
        super().__init__(name)
        self.outputs = (self.name, 'quakespasm.pak')

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/alexey-lysiuk/quakespasm-exp.git')

    def configure(self, state: BuildState):
        opts = state.options
        opts['CMAKE_EXE_LINKER_FLAGS'] = state.run_pkg_config('--libs', 'ogg', 'SDL2')
        opts['QUAKE_MACOS_BUNDLE'] = 'OFF'
        opts['QUAKE_MACOS_MOUSE_ACCELERATION'] = 'ON'

        super().configure(state)
