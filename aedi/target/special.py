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

import subprocess

from .base import Target
from ..state import BuildState


class CleanTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)
        self.args = ()

    def build(self, state: BuildState):
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
