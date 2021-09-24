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

import pathlib
import shlex
import zipapp

from .base import *


class SingleExeCTarget(MakeTarget):
    def __init__(self, name=None):
        super().__init__(name)
        self.options = ()

    def configure(self, state: BuildState):
        super().configure(state)

        for option in self.options:
            state.options[option] = None

    def build(self, state: BuildState):
        c_compiler = state.c_compiler()
        assert c_compiler

        args = [str(c_compiler), '-O3', '-o', self.name] + state.options.to_list()

        for var in ('CFLAGS', 'LDFLAGS'):
            args += shlex.split(state.environment[var])

        subprocess.run(args, check=True, cwd=state.build_path)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class BuildCMakeTarget(CMakeTarget):
    def __init__(self, name='cmake'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/Kitware/CMake/releases/download/v3.21.1/cmake-3.21.1.tar.gz',
            'fac3915171d4dff25913975d712f76e69aef44bf738ba7b976793a458b4cfed4')

    def configure(self, state: BuildState):
        # Bootstrap native CMake binary
        boostrap_path = state.native_build_path / '__bootstrap__'
        boostrap_cmk_path = boostrap_path / 'Bootstrap.cmk'
        boostrap_cmake = boostrap_cmk_path / 'cmake'

        if state.architecture() == machine():
            if not boostrap_cmake.exists():
                os.makedirs(boostrap_path, exist_ok=True)

                args = (state.source / 'configure', '--parallel=' + state.jobs)
                subprocess.run(args, cwd=boostrap_path)

                assert boostrap_cmake.exists()

        # The following variables are needed for cross-compilation
        opts = state.options
        opts['HAVE_POLL_FINE_EXITCODE'] = '0'
        opts['HAVE_POLL_FINE_EXITCODE__TRYRUN_OUTPUT'] = '0'

        env = state.environment
        env['PATH'] = os.pathsep.join([str(boostrap_cmk_path), env['PATH']])

        super().configure(state)

    def post_build(self, state: BuildState):
        self.install(state)


class GmakeTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='gmake'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/make/make-4.3.tar.lz',
            'de1a441c4edf952521db30bfca80baae86a0ff1acd0a00402999344f04c45e82')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('doc/make.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, 'make', self.name)


class MesonTarget(BuildTarget):
    def __init__(self, name='meson'):
        super().__init__(name)
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/mesonbuild/meson/releases/download/0.58.1/meson-0.58.1.tar.gz',
            '3144a3da662fcf79f1e5602fa929f2821cba4eba28c2c923fe0a7d3e3db04d5d')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('meson.py')

    def post_build(self, state: BuildState):
        dest_path = state.install_path / 'bin'
        os.makedirs(dest_path)

        def directory_filter(path: pathlib.Path) -> bool:
            return path.parts[0].startswith('mesonbuild')

        zipapp.create_archive(source=state.source, target=dest_path / self.name,
                              interpreter='/usr/bin/env python3', main='mesonbuild.mesonmain:main',
                              filter=directory_filter, compressed=True)


class NasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.xz',
            '3caf6729c1073bf96629b57cee31eeb54f4f8129b01902c73428836550b30a3f')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('nasm.txt')


class NinjaTarget(MakeTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ninja-build/ninja/archive/v1.10.2.tar.gz',
            'ce35865411f0490368a8fc383f29071de6690cbadc27704734978221f25e2bed')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('src/ninja.cc')

    def build(self, state: BuildState):
        cmdlines = (
            ('python3', './configure.py', '--verbose'),
            ('ninja', '--verbose'),
        )

        for args in cmdlines:
            subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


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
            '33db3cf9dc70ae704e1bbfba52c984f4c6dbfd0cc4449fa16408910e22b4fd90')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('pbzx.c')


class PkgConfigTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='pkg-config'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz',
            '6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('pkg-config.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, new_filename=self.name + '.exe')


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


class YasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libyasm.h')


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
