#
#    Helper module to build macOS version of various source ports
#    Copyright (C) 2020-2022 Alexey Lysiuk
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

import hashlib
import os
import re
import shutil
import subprocess
import typing
import urllib.request
from distutils.version import StrictVersion
from pathlib import Path

from .utility import CommandLineOptions


class BuildState:
    def __init__(self):
        self_path = Path(__file__)
        self.root_path = self_path.parent.parent
        self.deps_path = self.root_path / 'deps'
        self.prefix_path = self.root_path / 'prefix'
        self.bin_path = self.prefix_path / 'bin'
        self.include_path = self.prefix_path / 'include'
        self.lib_path = self.prefix_path / 'lib'
        self.patch_path = self.root_path / 'patch'
        self.source_path = self.root_path / 'source'
        self.temp_path = self.root_path / 'temp'

        self.source = Path()
        self.external_source = True

        self.build_path = None
        self.native_build_path = None

        self.output_path = None
        self.install_path = None

        self.platform = None
        self.xcode = False
        self.verbose = False
        self.jobs = 1

        self.static_moltenvk = False
        self.quasi_glib = False

        self.environment = os.environ.copy()
        self.options = CommandLineOptions()

    def architecture(self) -> str:
        return self.platform.architecture if self.platform else ''

    def host(self) -> str:
        return self.platform.host if self.platform else ''

    def os_version(self) -> StrictVersion:
        return self.platform.os_version if self.platform else None

    def sdk_path(self) -> Path:
        return self.platform.sdk_path if self.platform else None

    def sdk_version(self) -> typing.Union[StrictVersion, None]:
        if sdk_path := self.sdk_path():
            if match := re.search(r'/MacOSX(\d+.\d+).sdk', str(sdk_path), re.IGNORECASE):
                return StrictVersion(match[1])

        return None

    def c_compiler(self) -> Path:
        return self.platform.c_compiler if self.platform else None

    def cxx_compiler(self) -> Path:
        return self.platform.cxx_compiler if self.platform else None

    def checkout_git(self, url: str, branch: str = None):
        if self.source.exists():
            return

        args = ('git', 'clone', '--recurse-submodules', url, self.source)
        subprocess.run(args, check=True, cwd=self.root_path, env=self.environment)

        if branch:
            args = ('git', 'checkout', '-b', branch, 'origin/' + branch)
            subprocess.run(args, check=True, cwd=self.source, env=self.environment)

    def download_source(self, url: str, checksum: str, patches: typing.Union[tuple, list, str] = None):
        if self.external_source:
            return

        os.makedirs(self.source, exist_ok=True)

        data, filepath = self._read_source_package(url)
        self._verify_checksum(checksum, data, filepath)

        first_path_component, extract_path = self._unpack_source_package(filepath)

        if not patches:
            pass
        elif isinstance(patches, str):
            self._apply_source_patch(extract_path, patches)
        elif isinstance(patches, (tuple, list)):
            for patch in patches:
                self._apply_source_patch(extract_path, patch)
        else:
            assert False

        # Adjust source and build paths according to extracted source code
        self.source = extract_path
        self.build_path = self.build_path / first_path_component

    def _read_source_package(self, url: str) -> typing.Tuple[bytes, Path]:
        filename = url.rsplit(os.sep, 1)[1]
        filepath = self.source / filename

        if filepath.exists():
            # Read existing source package
            with open(filepath, 'rb') as f:
                data = f.read()
        else:
            # Download package with source code
            print(f'Downloading {filename}')

            response = urllib.request.urlopen(url)

            try:
                with open(filepath, 'wb') as f:
                    data = response.read()
                    f.write(data)

            except IOError:
                os.unlink(filepath)
                raise

        return data, filepath

    @staticmethod
    def _verify_checksum(checksum: str, data: bytes, filepath: Path) -> None:
        file_hasher = hashlib.sha256()
        file_hasher.update(data)
        file_checksum = file_hasher.hexdigest()

        if file_checksum != checksum:
            filepath.unlink()
            raise Exception(f'Checksum of {filepath} does not match, expected: {checksum}, actual: {file_checksum}')

    def _unpack_source_package(self, filepath: Path) -> typing.Tuple[str, Path]:
        args = ('tar', '-tf', filepath)
        result = subprocess.run(args, check=True, env=self.environment, stdout=subprocess.PIPE)

        file_paths_str = result.stdout.decode("utf-8")
        file_paths = file_paths_str.split('\n')
        first_path_component = None

        for path in file_paths:
            if os.sep in path:
                first_path_component = path[:path.find(os.sep)]
                break

        if not first_path_component:
            raise Exception(f'Failed to figure out source code path for {filepath}')

        extract_path = self.source / first_path_component

        if not extract_path.exists():
            # Extract source code package
            try:
                args = ('tar', '-xf', filepath)
                subprocess.run(args, check=True, cwd=self.source, env=self.environment)
            except (IOError, subprocess.CalledProcessError):
                shutil.rmtree(extract_path, ignore_errors=True)
                raise

        return first_path_component, extract_path

    def _apply_source_patch(self, extract_path: Path, patch: str):
        patch_path = self.patch_path / (patch + '.diff')
        assert patch_path.exists()

        # Check if patch is already applied
        test_arg = '--dry-run'
        args = ['patch', test_arg, '--strip=1', '--input=' + str(patch_path)]

        if subprocess.run(args, cwd=extract_path, env=self.environment).returncode == 0:
            # Patch wasn't applied yet, do it now
            args.remove(test_arg)
            subprocess.run(args, check=True, cwd=extract_path, env=self.environment)

    def run_pkg_config(self, *args) -> str:
        os.makedirs(self.build_path, exist_ok=True)

        args = (self.bin_path / 'pkg-config',) + args
        result = subprocess.run(args, check=True, cwd=self.build_path, env=self.environment, stdout=subprocess.PIPE)

        return result.stdout.decode('utf-8').rstrip('\n')

    def has_source_file(self, path: typing.Union[str, Path]):
        return (self.source / path).exists()

    def update_environment(self, name: str, value: str):
        env = self.environment
        env[name] = env[name] + ' ' + value if name in env else value

    def set_sdk(self, var_name: str):
        sdk_path = self.sdk_path()
        if sdk_path:
            self.update_environment(var_name, f'-isysroot {sdk_path}')

    def set_os_version(self, var_name: str):
        os_version = self.os_version()
        if os_version:
            self.update_environment(var_name, f'-mmacosx-version-min={os_version}')
