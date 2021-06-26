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

import shlex
import zipapp

from .base import *
from ..state import BuildState


class GmakeTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='gmake'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/make/make-4.3.tar.lz',
            'de1a441c4edf952521db30bfca80baae86a0ff1acd0a00402999344f04c45e82')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'doc/make.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, 'make', self.name)


class MesonTarget(BuildTarget):
    def __init__(self, name='meson'):
        super().__init__(name)
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/mesonbuild/meson/releases/download/0.56.0/meson-0.56.0.tar.gz',
            '291dd38ff1cd55fcfca8fc985181dd39be0d3e5826e5f0013bf867be40117213')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'meson.py')

    def post_build(self, state: BuildState):
        script = '__main__.py'
        shutil.copy(state.source + script, state.build_path)

        module = 'mesonbuild'
        module_path = state.build_path + module
        if os.path.exists(module_path):
            shutil.rmtree(module_path)
        shutil.copytree(state.source + module, module_path)

        dest_path = state.install_path + 'bin' + os.sep
        os.makedirs(dest_path, exist_ok=True)

        zipapp.create_archive(state.build_path, dest_path + self.name, '/usr/bin/env python3', compressed=True)


class NasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.xz',
            '3caf6729c1073bf96629b57cee31eeb54f4f8129b01902c73428836550b30a3f')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'nasm.txt')


class NinjaTarget(MakeTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ninja-build/ninja/archive/v1.10.2.tar.gz',
            'ce35865411f0490368a8fc383f29071de6690cbadc27704734978221f25e2bed')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'src/ninja.cc')

    def build(self, state: BuildState):
        cmdlines = (
            ('python3', './configure.py', '--verbose'),
            ('ninja', '--verbose'),
        )

        for args in cmdlines:
            subprocess.run(args, check=True, cwd=state.build_path, env=self.environment)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class PkgConfigTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='pkg-config'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz',
            '6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'pkg-config.1')

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, new_filename=self.name + '.exe')


class YasmTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, state: BuildState) -> bool:
        return os.path.exists(state.source + 'libyasm.h')


class ZipTarget(MakeTarget):
    def __init__(self, name='zip'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/infozip/Zip%203.x%20%28latest%29/3.0/zip30.tar.gz',
            'f0e8bb1f9b7eb0b01285495a2699df3a4b766784c1765a8f1aeedf63c0806369',
            patches='zip-fix-misc')

    def build(self, state: BuildState):
        args = [
            state.c_compiler(),
            '-O3', '-I.', '-DUNIX',
            '-DBZIP2_SUPPORT', '-DLARGE_FILE_SUPPORT', '-DUNICODE_SUPPORT',
            '-DHAVE_DIRENT_H', '-DHAVE_TERMIOS_H',
            'crc32.c', 'crypt.c', 'deflate.c', 'fileio.c', 'globals.c', 'trees.c',
            'ttyio.c', 'unix/unix.c', 'util.c', 'zip.c', 'zipfile.c', 'zipup.c',
            '-lbz2', '-o', 'zip'
        ]

        for var in ('CFLAGS', 'LDFLAGS'):
            args += shlex.split(self.environment[var])

        subprocess.run(args, check=True, cwd=state.build_path)

    def post_build(self, state: BuildState):
        bin_path = state.install_path + 'bin'
        os.makedirs(bin_path, exist_ok=True)
        shutil.copy(state.build_path + 'zip', bin_path)
