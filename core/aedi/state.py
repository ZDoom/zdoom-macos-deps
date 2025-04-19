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

import hashlib
import os
import re
import shutil
import subprocess
import sys
import typing
import urllib.request
from pathlib import Path

from .packaging.version import Version as StrictVersion
from .utility import CommandLineOptions


class BuildState:
    def __init__(self):
        core_path = Path(__file__).parent.parent.absolute()
        entry_script = Path(sys.argv[0]).absolute()
        self.root_path = entry_script.parent
        self.core_deps_path = core_path / 'deps'
        self.deps_path = self.root_path / 'deps'
        self.prefix_path = self.root_path / 'prefix'
        self.bin_path = self.prefix_path / 'bin'
        self.include_path = self.prefix_path / 'include'
        self.lib_path = self.prefix_path / 'lib'
        self.core_patch_path = core_path / 'patch'
        self.patch_path = self.root_path / 'patch'
        self.source_path = self.root_path / 'source'
        self.temp_path = self.root_path / 'temp'

        self.source = Path()
        self.external_source = True

        self.build_path = None
        self.native_build_path = None

        self.output_path = None
        self.install_path = None

        self._compiler_flags = None
        self._linker_flags = None

        self.platform = None
        self.xcode = False
        self.verbose = False
        self.jobs = 1

        self.arguments = None
        self.environment = os.environ.copy()
        self.environment['PKG_CONFIG_PATH'] = str(self.lib_path / 'pkgconfig')
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

    def compiler_flags(self) -> str:
        if not self._compiler_flags:
            self._compiler_flags = f'-I{self.include_path} -ffile-prefix-map={self.source}/='

        return self._compiler_flags

    def linker_flags(self) -> str:
        if not self._linker_flags:
            self._linker_flags = f'-L{self.lib_path}'

            version_output = subprocess.run(('clang', '--version'), check=True, capture_output=True)
            version_match = re.search(r'\(clang-([\d.]+)\)', version_output.stdout.decode('ascii'))

            if version_match:
                version = StrictVersion(version_match.group(1))

                if version.major >= 1500:
                    # Silence ld: warning: ignoring duplicate libraries: '...'
                    self._linker_flags += ' -Wl,-no_warn_duplicate_libraries'

                if version.major == 1500 and version.minor == 0:
                    # Fix for Xcode 15.0 known issue with the new linker
                    # https://developer.apple.com/documentation/xcode-release-notes/xcode-15-release-notes#Known-Issues
                    # Binaries using symbols with a weak definition crash at runtime on iOS 14/macOS 12 or older.
                    # This impacts primarily C++ projects due to their extensive use of weak symbols. (114813650) (FB13097713)
                    # Workaround: Bump the minimum deployment target to iOS 15, macOS 12, watchOS 8 or tvOS 15,
                    # or add -Wl,-ld_classic to the OTHER_LDFLAGS build setting.
                    self._linker_flags += ' -Wl,-ld_classic'

        return self._linker_flags

    def checkout_git(self, url: str, branch: typing.Optional[str] = None):
        if self.source.exists():
            return

        args = ('git', 'clone', '--recurse-submodules', url, self.source)
        subprocess.run(args, check=True, cwd=self.root_path, env=self.environment)

        if branch:
            args = ('git', 'checkout', '-b', branch, 'origin/' + branch)
            subprocess.run(args, check=True, cwd=self.source, env=self.environment)

    def download_source(self, url: str, checksum: str, patches: typing.Union[tuple, list, str, None] = None):
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
        file_paths.remove('')
        assert len(file_paths) > 0

        # Determine root path of source code to be extracted
        # If all files and directories are stored in one top level directory, this directory is used as a root
        # If there is no single top level directory, new root directory will be created
        need_new_directory = False
        first_path_component = ''

        for path in file_paths:
            if os.sep not in path:
                need_new_directory = True
                break
            else:
                current_first_path_component = path[:path.find(os.sep)]

                if first_path_component:
                    if first_path_component != current_first_path_component:
                        need_new_directory = True
                        break
                else:
                    first_path_component = current_first_path_component

        work_path = self.source

        if need_new_directory:
            first_path_component = Path(filepath.name).stem
            work_path /= first_path_component

        extract_path = self.source / first_path_component

        if not extract_path.exists():
            os.makedirs(work_path, exist_ok=True)

            # Extract source code package
            try:
                args = ('tar', '-xf', filepath)
                subprocess.run(args, check=True, cwd=work_path, env=self.environment)
            except (IOError, subprocess.CalledProcessError):
                shutil.rmtree(extract_path, ignore_errors=True)
                raise

        return first_path_component, extract_path

    def _apply_source_patch(self, extract_path: Path, patch: str):
        patch_filename = patch + '.diff'
        patch_path = self.patch_path / patch_filename

        if not patch_path.exists():
            patch_path = self.core_patch_path / patch_filename

        assert patch_path.exists()

        args = ['patch', '--strip=1', '--input=' + str(patch_path)]

        # Check if patch is already applied
        dry_run_args = args + ['--dry-run', '--force']
        dry_run = subprocess.run(dry_run_args, cwd=extract_path, env=self.environment,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if dry_run.returncode == 0:
            # Patch wasn't applied yet, do it now
            subprocess.run(args, check=True, cwd=extract_path, env=self.environment)

    def run_pkg_config(self, *args) -> str:
        os.makedirs(self.build_path, exist_ok=True)

        args = (
            self.bin_path / 'pkg-config',
            f'--define-variable=prefix={self.prefix_path}',
            '--static',
        ) + args
        result = subprocess.run(args, check=True, cwd=self.build_path, env=self.environment, stdout=subprocess.PIPE)

        return result.stdout.decode('utf-8').rstrip('\n')

    def has_source_file(self, path: typing.Union[str, Path]):
        return (self.source / path).exists()

    def update_flags_environment_variable(self, name: str, value: str):
        sdk_path = self.sdk_path()
        if sdk_path:
            value += f' -isysroot {sdk_path}'

        os_version = self.os_version()
        if os_version:
            value += f' -mmacosx-version-min={os_version}'

        env = self.environment
        env[name] = env[name] + ' ' + value if name in env else value

    def validate_minimum_version(self, version: str):
        minimum_version = StrictVersion(version)

        if os_version := self.os_version():
            if os_version < minimum_version:
                raise RuntimeError('Minimum OS version requirement is not met')

        if sdk_version := self.sdk_version():
            if sdk_version < minimum_version:
                raise RuntimeError('Minimum SDK version requirement is not met')

    def source_version(self):
        version = ''

        args = ('git', f'--git-dir={self.source}/.git', 'describe', '--tags')
        git_describe = subprocess.run(args, env=self.environment, capture_output=True)

        if git_describe.returncode == 0:
            version = git_describe.stdout.decode('ascii')

        return version
