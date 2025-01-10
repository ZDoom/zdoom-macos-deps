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

import shlex
import shutil
import subprocess

from ..state import BuildState
from . import base


class BuildPrefix(base.Target):
    def __init__(self, name='build-prefix'):
        super().__init__(name)


class CleanTarget(base.Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.args = ()

    def build(self, state: BuildState):
        assert not state.xcode

        args = ('git', 'clean') + self.args
        subprocess.run(args, check=True, cwd=state.root_path, env=state.environment)


class CleanAllTarget(CleanTarget):
    def __init__(self, name='clean-all'):
        super().__init__(name)
        self.args = ('-dX', '--force')


class CleanDepsTarget(CleanAllTarget):
    def __init__(self, name='clean-deps'):
        super().__init__(name)

    def configure(self, state: BuildState):
        self.args += (state.deps_path,)


class DownloadCMakeTarget(base.Target):
    def __init__(self, name='download-cmake'):
        super().__init__(name)

    def build(self, state: BuildState):
        cmake_version = '3.21.1'
        cmake_basename = f'cmake-{cmake_version}-macos10.10-universal'
        cmake_url = f'https://github.com/Kitware/CMake/releases/download/v{cmake_version}/{cmake_basename}.tar.gz'
        state.download_source(cmake_url, '20dbede1d80c1ac80be2966172f8838c3d899951ac4467372f806b386d42ad3c')

        target_path = state.deps_path / 'cmake'
        if target_path.exists():
            shutil.rmtree(target_path)
        target_path.mkdir()

        source_path = state.source / 'CMake.app' / 'Contents'
        shutil.move(str(source_path / 'bin'), target_path)
        shutil.move(str(source_path / 'share'), target_path)
        shutil.rmtree(state.source)


class TestDepsTarget(base.BuildTarget):
    def __init__(self, name='test-deps'):
        super().__init__(name)
        self.multi_platform = False

    def build(self, state: BuildState):
        assert not state.xcode

        test_path = state.root_path / 'test'

        for entry in test_path.iterdir():
            if not entry.name.endswith('.cpp'):
                continue

            test_name = entry.stem
            pkg_config_output = state.run_pkg_config('--cflags', '--libs', test_name)
            exe_path = state.build_path / test_name

            print('Testing ' + test_name)

            build_args = [
                'clang++',
                '-arch', 'x86_64',
                '-arch', 'arm64',
                '-std=c++17',
                '-include', test_path / 'aedi.h',
                '-g',
                '-o', exe_path,
                entry,
            ]
            build_args += shlex.split(pkg_config_output)
            build_args += shlex.split(state.linker_flags())

            if state.verbose:
                print(' '.join(str(arg) for arg in build_args))

            for args in (build_args, (exe_path,)):
                subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)
