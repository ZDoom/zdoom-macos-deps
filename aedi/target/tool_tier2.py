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

import os
import subprocess

from ..state import BuildState
from . import base


class DzipTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='dzip'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/kugelrund/dzip/archive/refs/tags/v3.1.tar.gz',
            '9f057e35ef5ddda1a0911b8f877a41b2934669377cb053b45364ddb72716b520')


class GlslangTarget(base.CMakeStaticDependencyTarget):
    # Build with --os-version-x64=10.15 command line option

    def __init__(self, name='glslang'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/glslang/archive/refs/tags/13.1.1.tar.gz',
            '1c4d0a5a38c8aaf89a2d7e6093be734320599f5a6775b2726beeb05b0c054e66')

    def configure(self, state: BuildState):
        args = ('python3', 'update_glslang_sources.py')
        subprocess.run(args, check=True, cwd=state.source, env=state.environment)

        state.validate_minimum_version('10.15')  # SPIRV-Tools uses <filesystem>
        state.options['ENABLE_CTEST'] = 'NO'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        # Remove shared library
        lib_path = state.install_path / 'lib'
        os.unlink(lib_path / 'libSPIRV-Tools-shared.dylib')

        lib_cmake_path = lib_path / 'cmake'
        spirv_tools_module = lib_cmake_path / 'SPIRV-Tools/SPIRV-ToolsTarget-release.cmake'
        self.keep_module_target(state, 'SPIRV-Tools-static', (spirv_tools_module,))

        # Remove deprecated files with absolute paths in them
        for entry in os.listdir(lib_cmake_path):
            if entry.endswith('.cmake'):
                os.unlink(lib_cmake_path / entry)


class P7ZipTarget(base.CMakeTarget):
    def __init__(self, name='p7zip'):
        super().__init__(name)
        self.src_root = 'CPP/7zip/CMAKE/7za'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/p7zip-project/p7zip/archive/refs/tags/v17.04.tar.gz',
            'ea029a2e21d2d6ad0a156f6679bd66836204aa78148a4c5e498fe682e77127ef')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('CPP/7zip/CMAKE/CMakeLists.txt') \
            and state.has_source_file('C/fast-lzma2/fast-lzma2.h')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, '7za')


class PbzxTarget(base.SingleExeCTarget):
    def __init__(self, name='pbzx'):
        super().__init__(name)
        self.options = ('pbzx.c', '-lxar', '-llzma')

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/nrosenstein-stuff/pbzx/archive/refs/tags/v1.0.2.tar.gz',
            '33db3cf9dc70ae704e1bbfba52c984f4c6dbfd0cc4449fa16408910e22b4fd90',
            'pbzx-xar-content')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('pbzx.c')


class QPakManTarget(base.CMakeTarget):
    def __init__(self, name='qpakman'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/bunder/qpakman/archive/refs/tags/v0.67.tar.gz',
            '0b2cfc0e66a6ea3f0e332409254e06f78f5bb9b47f6b134b90681468d701d421')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class Radare2Target(base.MesonTarget):
    def __init__(self, name='radare2'):
        super().__init__(name)
        self.configure_prefix = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/radareorg/radare2/releases/download/5.8.8/radare2-5.8.8.tar.xz',
            '070dbc353e8e0d09fb985a73bfee2783690abbd58d4fbbecc3a50480eab9d537')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('man/radare2.1')

    def configure(self, state: BuildState):
        option = state.options
        option['blob'] = 'true'
        option['enable_tests'] = 'false'
        option['enable_r2r'] = 'false'
        option['r2_gittip'] = 'ea7f0356519884715cf1d5fba16042bac72b2df5'
        option['r2_version_commit'] = '1'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        bin_path = state.install_path / 'bin'
        os.unlink(bin_path / 'r2blob.static')
        os.rename(bin_path / 'r2blob', bin_path / 'radare2')


class RizinTarget(base.MesonTarget):
    def __init__(self, name='rizin'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/rizinorg/rizin/releases/download/v0.6.2/rizin-src-v0.6.2.tar.xz',
            'e29a00a3e22004bdd10146d286b1cce0e06196d41aae4729aafc9d78321ff86b')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('binrz/man/rizin.1')

    def configure(self, state: BuildState):
        option = state.options
        option['blob'] = 'true'
        option['enable_tests'] = 'false'
        option['enable_rz_test'] = 'false'
        option['local'] = 'enabled'
        option['portable'] = 'true'

        super().configure(state)


class SeverZipTarget(base.MakeTarget):
    # Build with --os-version-x64=10.13 command line option

    def __init__(self, name='7zip'):
        super().__init__(name)
        self.src_root = 'CPP/7zip/Bundles/Alone2'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://7-zip.org/a/7z2301-src.tar.xz',
            '356071007360e5a1824d9904993e8b2480b51b570e8c9faf7c0f58ebe4bf9f74',
            patches='7zip-fix-errors')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('CPP/7zip/cmpl_mac_arm64.mak')

    def configure(self, state: BuildState):
        state.validate_minimum_version('10.13')
        super().configure(state)

    def build(self, state: BuildState):
        environment = state.environment
        mak_suffix = self._arch_suffix(state)

        opts = state.options
        opts['-f'] = None
        opts[f'../../cmpl_mac_{mak_suffix}.mak'] = None
        opts['CFLAGS_BASE_LIST'] = environment['CFLAGS'] + ' -c'
        opts['LDFLAGS_STATIC_2'] = environment['LDFLAGS']

        super().build(state)

    def post_build(self, state: BuildState):
        build_suffix = self._arch_suffix(state)
        self.copy_to_bin(state, f'{self.src_root}/b/m_{build_suffix}/7zz', '7zz')

    @staticmethod
    def _arch_suffix(state: BuildState):
        arch = state.architecture()
        return 'x64' if arch == 'x86_64' else arch


class UnrarTarget(base.MakeTarget):
    def __init__(self, name='unrar'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.rarlab.com/rar/unrarsrc-6.0.7.tar.gz',
            'a7029942006cbcced3f3b7322ec197683f8e7be408972ca08099b196c038f518')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('rar.hpp')


class ZipTarget(base.SingleExeCTarget):
    def __init__(self, name='zip'):
        super().__init__(name)
        self.options = (
            '-I.', '-DUNIX', '-DBZIP2_SUPPORT', '-DLARGE_FILE_SUPPORT', '-DUNICODE_SUPPORT',
            '-DHAVE_DIRENT_H', '-DHAVE_TERMIOS_H', '-lbz2',
            'crc32.c', 'crypt.c', 'deflate.c', 'fileio.c', 'globals.c', 'trees.c',
            'ttyio.c', 'unix/unix.c', 'util.c', 'zip.c', 'zipfile.c', 'zipup.c',
        )

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/infozip/Zip%203.x%20%28latest%29/3.0/zip30.tar.gz',
            'f0e8bb1f9b7eb0b01285495a2699df3a4b766784c1765a8f1aeedf63c0806369',
            patches='zip-fix-misc')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('zip.h')
