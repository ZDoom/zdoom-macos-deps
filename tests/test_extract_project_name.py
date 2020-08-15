#!/usr/bin/env python3

#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020 Alexey Lysiuk
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
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '..')
sys.dont_write_bytecode = True

from build import Builder  # pylint: disable=import-error

test_lines = (
    'project(GZDoom)',
    'project("PrBoom-Plus" VERSION 2.5.1.7)',
    'project("Chocolate Doom" VERSION 3.0.0 LANGUAGES C)',
    'PROJECT(doomretro C)',
    'project(DevilutionX',
)

for line in test_lines:
    project_name = Builder.extract_project_name(line)
    assert project_name
    print(project_name)
