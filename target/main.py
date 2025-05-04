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
import shutil
from pathlib import Path
from platform import machine

from aedi.state import BuildState
from aedi.target.base import CMakeMainTarget, CMakeSingleExeMainTarget


def _force_cross_compilation(state: BuildState):
    if state.architecture() == machine():
        return

    opts = state.options
    opts['FORCE_CROSSCOMPILE'] = 'YES'
    opts['IMPORT_EXECUTABLES'] = state.native_build_path / 'ImportExecutables.cmake'


def _force_openal_soft(state: BuildState):
    # Explicit OpenAL configuration to avoid selection of Apple's framework
    opts = state.options
    opts['OPENAL_INCLUDE_DIR'] = state.include_path / 'AL'
    opts['OPENAL_LIBRARY'] = state.lib_path / 'libopenal.a'


class ZDoomBaseTarget(CMakeMainTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        pkg_config_args = ['--libs', 'openal', 'sndfile']
        linker_flags = ''

        if state.arguments.quasi_glib:
            linker_flags += '-lquasi-glib '
        else:
            pkg_config_args.append('glib-2.0')

        opts = state.options
        opts['CMAKE_EXE_LINKER_FLAGS'] += linker_flags + state.run_pkg_config(*pkg_config_args)
        opts['PK3_QUIET_ZIPDIR'] = 'YES'
        opts['DYN_OPENAL'] = 'NO'

        _force_cross_compilation(state)
        _force_openal_soft(state)

        super().configure(state)


class ZDoomVulkanBaseTarget(ZDoomBaseTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        if state.arguments.static_moltenvk:
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
        if not state.arguments.static_moltenvk:
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
                copy_func = os.symlink if state.xcode else shutil.copy
                copy_func(src_path, dst_path)  # type: ignore

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


class VkDoomTarget(ZDoomVulkanBaseTarget):
    def __init__(self, name='vkdoom'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.checkout_git('https://github.com/dpjudas/VkDoom.git')


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
