#!/usr/bin/env python3

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
import sys


def _build(source_file: str):
    self_path = os.path.dirname(os.path.abspath(__file__))
    pkg_config_path = os.path.abspath(self_path + '/../prefix/bin/pkg-config')

    args = (
        pkg_config_path,
        '--cflags', '--libs',
        os.path.splitext(source_file)[0]
    )
    pkg_config_output = subprocess.check_output(args, cwd=self_path)
    pkg_config_output = pkg_config_output.decode('utf-8').strip('\n')

    args = [
        'clang',
        '-arch', 'x86_64',
        '-arch', 'arm64',
        source_file
    ]
    args += shlex.split(pkg_config_output)
    subprocess.check_call(args, cwd=self_path)


def _main():
    if len(sys.argv) == 1:
        test_path = os.path.dirname(os.path.abspath(__file__))
        tests = [entry.name for entry in os.scandir(test_path) if entry.name.endswith('.cpp')]
    else:
        tests = sys.argv[1:]

    for test in tests:
        _build(test)


if __name__ == '__main__':
    _main()
