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
            'https://github.com/KhronosGroup/glslang/archive/refs/tags/11.13.0.tar.gz',
            '592c98aeb03b3e81597ddaf83633c4e63068d14b18a766fd11033bad73127162')

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
            'https://github.com/jinfeihan57/p7zip/archive/refs/tags/v17.04.tar.gz',
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
