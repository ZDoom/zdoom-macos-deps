#
#    Module to build various libraries and tools for macOS
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
            'https://github.com/Kitware/CMake/releases/download/v3.31.4/cmake-3.31.4.tar.gz',
            'a6130bfe75f5ba5c73e672e34359f7c0a1931521957e8393a5c2922c8b0f7f25')

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

        env = state.environment
        env['PATH'] = os.pathsep.join([str(boostrap_cmk_path), env['PATH']])

        super().configure(state)

    def post_build(self, state: BuildState):
        self.install(state)


class GmakeTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='gmake'):
        super().__init__(name)

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
            'https://github.com/mesonbuild/meson/releases/download/1.7.2/meson-1.7.2.tar.gz',
            '4d40d63aa748a9c139cc41ab9bffe43edd113c5639d78bde81544ca955aea890')

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
            # 'https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/nasm-2.16.03.tar.xz',
            'https://fossies.org/linux/misc/nasm-2.16.03.tar.xz',
            '1412a1c760bbd05db026b6c0d1657affd6631cd0a63cddb6f73cc6d4aa616148',
            patches='nasm-deterministic-date')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('nasm.txt')


class NinjaTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='ninja'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/ninja-build/ninja/archive/refs/tags/v1.12.1.tar.gz',
            '821bdff48a3f683bc4bb3b6f0b5fe7b2d647cf65d52aeb63328c91a6c6df285a')

    def configure(self, state: BuildState):
        state.options['BUILD_TESTING'] = 'NO'
        super().configure(state)


class PkgconfTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='pkgconf'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://distfiles.ariadne.space/pkgconf/pkgconf-2.4.3.tar.xz',
            '51203d99ed573fa7344bf07ca626f10c7cc094e0846ac4aa0023bd0c83c25a41')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libpkgconf/libpkgconf.h')

    def configure(self, state: BuildState):
        hardcoded_prefix = '/usr/local'
        hardcoded_libdir = hardcoded_prefix + '/lib'
        hardcoded_pkgdir = hardcoded_libdir + '/pkgconfig'

        opts = state.options
        opts['--with-personality-dir'] = hardcoded_pkgdir + '/personality.d'
        opts['--with-pkg-config-dir'] = hardcoded_pkgdir
        opts['--with-system-includedir'] = hardcoded_prefix + '/include'
        opts['--with-system-libdir'] = hardcoded_libdir

        super().configure(state)

    def post_build(self, state: BuildState):
        self.copy_to_bin(state)


class YasmTarget(base.ConfigureMakeDependencyTarget):
    def __init__(self, name='yasm'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz',
            '3dce6601b495f5b3d45b59f7d2492a340ee7e84b5beca17e48f862502bd5603f')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libyasm.h')
