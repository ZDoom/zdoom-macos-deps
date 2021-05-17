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

import os
import shlex
import subprocess

from .base import Target, BuildTarget
from ..state import BuildState


class CleanTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.args = ()

    def build(self, state: BuildState):
        assert not state.xcode

        args = ('git', 'clean') + self.args
        subprocess.check_call(args, cwd=state.root_path)


class CleanAllTarget(CleanTarget):
    def __init__(self, name='clean-all'):
        super().__init__(name)
        self.args = ('-dX', '--force')


class CleanDepsTarget(CleanAllTarget):
    def __init__(self, name='clean-deps'):
        super().__init__(name)

    def configure(self, state: BuildState):
        self.args += (state.deps_path,)


class TestDepsTarget(BuildTarget):
    def __init__(self, name='test-deps'):
        super().__init__(name)
        self.multi_platform = False

    def build(self, state: BuildState):
        assert not state.xcode

        test_path = state.root_path + 'test'

        for entry in os.scandir(test_path):
            if not entry.name.endswith('.cpp'):
                continue

            test_name = os.path.splitext(entry.name)[0]
            pkg_config_output = state.run_pkg_config('--cflags', '--libs', test_name)
            exe_name = state.build_path + test_name

            print('Testing ' + test_name)

            args = [
                'clang',
                '-arch', 'x86_64',
                '-arch', 'arm64',
                '-std=c++17',
                '-include', os.path.join(test_path, 'aedi.h'),
                '-o', exe_name,
                entry.path,
            ]
            args += shlex.split(pkg_config_output)
            subprocess.run(args, cwd=state.build_path, check=True)
            subprocess.run((exe_name,), check=True)
