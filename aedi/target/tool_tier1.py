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
import pathlib
import platform
import subprocess
import zipapp

from ..state import BuildState
from . import base


class CMakeTarget(base.CMakeTarget):
    def __init__(self, name='cmake'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/Kitware/CMake/releases/download/v3.25.1/cmake-3.25.1.tar.gz',
            '1c511d09516af493694ed9baf13c55947a36389674d657a2d5e0ccedc6b291d8')

    def configure(self, state: BuildState):
        # Bootstrap native CMake binary
        boostrap_path = state.native_build_path / '__bootstrap__'
        boostrap_cmk_path = boostrap_path / 'Bootstrap.cmk'
        boostrap_cmake = boostrap_cmk_path / 'cmake'

        if state.architecture() == platform.machine():
            if not boostrap_cmake.exists():
                os.makedirs(boostrap_path, exist_ok=True)

                args = (state.source / 'configure', '--parallel=' + state.jobs)
                subprocess.run(args, check=True, cwd=boostrap_path, env=state.environment)

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


class GmakeTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='gmake'):
        super().__init__(name)

        # Target's directory is removed before configuration step
        # gmake cannot be used to build itself, use system's make instead
        self.tool = 'make'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://ftp.gnu.org/gnu/make/make-4.4.1.tar.lz',
            '8814ba072182b605d156d7589c19a43b89fc58ea479b9355146160946f8cf6e9')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('doc/make.1')

    def configure(self, state: BuildState):
        opts = state.options
        opts['--datarootdir'] = '/usr/local/share'
        opts['--includedir'] = '/usr/local/include'
        opts['--libdir'] = '/usr/local/lib'

        super().configure(state)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state, 'make', self.name)


class MesonTarget(base.BuildTarget):
    def __init__(self, name='meson'):
        super().__init__(name)
        self.multi_platform = False

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/mesonbuild/meson/releases/download/1.3.0/meson-1.3.0.tar.gz',
            '4ba253ef60e454e23234696119cbafa082a0aead0bd3bbf6991295054795f5dc')

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


class NasmTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='nasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.nasm.us/pub/nasm/releasebuilds/2.16.02/nasm-2.16.02.tar.xz',
            '1e1b942ea88f22edae89659e15be26fa027eae0747f51413540f52d4eac4790d',
            patches='nasm-deterministic-date')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('nasm.txt')


class NinjaTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ninja-build/ninja/archive/refs/tags/v1.11.0.tar.gz',
            '3c6ba2e66400fe3f1ae83deb4b235faf3137ec20bd5b08c29bfc368db143e4c6')

    def configure(self, state: BuildState):
        state.options['BUILD_TESTING'] = 'NO'
        super().configure(state)


class PkgConfigTarget(base.ConfigureMakeDependencyTarget):
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


class YasmTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libyasm.h')
