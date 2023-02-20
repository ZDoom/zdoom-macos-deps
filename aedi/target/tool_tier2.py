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


class GlslangTarget(CMakeStaticDependencyTarget):
    def __init__(self, name='glslang'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/KhronosGroup/glslang/archive/refs/tags/12.0.0.tar.gz',
            '7cb45842ec1d4b6ea775d624c3d2d8ba9450aa416b0482b0cc7e4fdd399c3d75')

    def configure(self, state: BuildState):
        args = ('python3', 'update_glslang_sources.py')
        subprocess.run(args, check=True, cwd=state.source, env=state.environment)

        state.options['ENABLE_CTEST'] = 'NO'

        super().configure(state)


class P7ZipTarget(CMakeTarget):
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


class PbzxTarget(SingleExeCTarget):
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


class QPakManTarget(CMakeTarget):
    def __init__(self, name='qpakman'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/bunder/qpakman/archive/refs/tags/v0.67.tar.gz',
            '0b2cfc0e66a6ea3f0e332409254e06f78f5bb9b47f6b134b90681468d701d421')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class SeverZipTarget(MakeTarget):
    # Build with --os-version-x64=10.13 command line option

    def __init__(self, name='7zip'):
        super().__init__(name)
        self.src_root = 'CPP/7zip/Bundles/Alone2'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.7-zip.org/a/7z2201-src.tar.xz',
            '393098730c70042392af808917e765945dc2437dee7aae3cfcc4966eb920fbc5',
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


class UnrarTarget(MakeTarget):
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


class ZipTarget(SingleExeCTarget):
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
