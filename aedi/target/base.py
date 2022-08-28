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

import copy
import os
import re
import shutil
import subprocess
import typing
from pathlib import Path
from platform import machine

from ..state import BuildState
from ..utility import (
    OS_VERSION_ARM64,
    OS_VERSION_X86_64,
    CommandLineOptions,
    symlink_directory,
)


class Target:
    DESTINATION_DEPS = 0
    DESTINATION_OUTPUT = 1

    def __init__(self, name=None):
        self.name = name
        self.destination = self.DESTINATION_DEPS

        self.multi_platform = False
        self.unsupported_architectures = ()

    def prepare_source(self, state: BuildState):
        """ Called when target is selected by name """
        pass

    def initialize(self, state: BuildState):
        """ Called on all targets except the selected one before prefix directory creation """
        pass

    def detect(self, state: BuildState) -> bool:
        """
        Called when target is selected by source code directory
        Called on all targets until match is found
        """
        return False

    def configure(self, state: BuildState):
        """ Called before selected target is about to build """
        pass

    def build(self, state: BuildState):
        """ Does actual build """
        pass

    def post_build(self, state: BuildState):
        """ Called after selected target is built """
        pass


class BuildTarget(Target):
    def __init__(self, name=None):
        super().__init__(name)

        self.src_root = ''
        self.multi_platform = True

        self.os_version = dict()
        self.os_version['x86_64'] = OS_VERSION_X86_64
        self.os_version['arm64'] = OS_VERSION_ARM64

        self.sdk_version = dict()
        self.sdk_version['x86_64'] = OS_VERSION_X86_64
        self.sdk_version['arm64'] = OS_VERSION_ARM64

    def configure(self, state: BuildState):
        os_version = state.os_version()
        if os_version and os_version < self.os_version[state.architecture()]:
            raise RuntimeError('Minimum OS version requirement is not met')

        if sdk_version := state.sdk_version():
            if sdk_version < self.sdk_version[state.architecture()]:
                raise RuntimeError('Minimum SDK version requirement is not met')

        os.makedirs(state.build_path, exist_ok=True)

        env = state.environment
        env['PATH'] = os.pathsep.join([
            str(state.bin_path),
            env['PATH'],
        ])

        if state.xcode:
            return

        if c_compiler := state.c_compiler():
            env['CC'] = str(c_compiler)
        if cxx_compiler := state.cxx_compiler():
            env['CXX'] = str(cxx_compiler)

        for prefix in ('CPP', 'C', 'CXX', 'OBJC', 'OBJCXX'):
            var_name = f'{prefix}FLAGS'

            state.update_environment(var_name, f'-I{state.include_path}')
            state.set_sdk(var_name)
            state.set_os_version(var_name)

        ldflags = 'LDFLAGS'

        state.update_environment(ldflags, f'-L{state.lib_path}')
        state.set_sdk(ldflags)
        state.set_os_version(ldflags)

    def install(self, state: BuildState, options: CommandLineOptions = None, tool: str = 'gmake'):
        if state.xcode:
            return

        if state.install_path.exists():
            shutil.rmtree(state.install_path)

        args = [tool]
        args += options and options.to_list() or ['install']

        subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)

        self.update_pc_files(state)

    @staticmethod
    def update_text_file(path: Path, processor: typing.Callable = None):
        with open(path, 'r') as f:
            content = f.readlines()

        patched_content = []

        for line in content:
            patched_line = processor(line) if processor else line

            if patched_line:
                patched_content.append(patched_line)

        with open(path, 'w') as f:
            f.writelines(patched_content)

    @staticmethod
    def _update_variables_file(path: Path, prefix_value: str, processor: typing.Callable = None, quotes: bool = True):
        prefix = 'prefix='
        exec_prefix = 'exec_prefix='
        includedir = 'includedir='
        libdir = 'libdir='

        def quote(value: str) -> str:
            return f'"{value}"' if quotes else value

        def patch_proc(line: str) -> str:
            patched_line = line

            if line.startswith(prefix):
                patched_line = prefix + quote(prefix_value) + os.linesep
            elif line.startswith(exec_prefix):
                patched_line = exec_prefix + quote('${prefix}') + os.linesep
            elif line.startswith(includedir):
                patched_line = includedir + quote('${prefix}/include') + os.linesep
            elif line.startswith(libdir):
                patched_line = libdir + quote('${exec_prefix}/lib') + os.linesep

            if processor:
                patched_line = processor(path, patched_line)

            return patched_line

        BuildTarget.update_text_file(path, patch_proc)

    @staticmethod
    def update_config_script(path: Path, processor: typing.Callable = None):
        BuildTarget._update_variables_file(path, r'$(cd "${0%/*}/.."; pwd)', processor)

    @staticmethod
    def update_pc_file(path: Path, processor: typing.Callable = None):
        BuildTarget._update_variables_file(path, '', processor, quotes=False)

    def update_pc_files(self, state: BuildState):
        for root, _, files in os.walk(state.install_path, followlinks=True):
            for filename in files:
                if filename.endswith('.pc'):
                    file_path = Path(root) / filename
                    BuildTarget.update_pc_file(file_path, self._process_pkg_config)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        assert pcfile
        return line

    def write_pc_file(self, state: BuildState,
                      filename=None, name=None, description=None, version='',
                      requires='', requires_private='', libs='', libs_private='', cflags=''):
        pkgconfig_path = state.install_path / 'lib/pkgconfig'
        os.makedirs(pkgconfig_path, exist_ok=True)

        if not filename:
            filename = self.name + '.pc'
        if not name:
            name = self.name
        if not description:
            description = self.name
        if not libs:
            libs = '-l' + self.name

        pc_content = f'''prefix=
exec_prefix=${{prefix}}
libdir=${{exec_prefix}}/lib
includedir=${{prefix}}/include

Name: {name}
Description: {description}
Version: {version}
Requires: {requires}
Requires.private: {requires_private}
Libs: -L${{libdir}} {libs}
Libs.private: {libs_private}
Cflags: -I${{includedir}} {cflags}
'''
        with open(pkgconfig_path / filename, 'w') as f:
            f.write(pc_content)

    @staticmethod
    def make_platform_header(state: BuildState, header: str):
        include_path = state.install_path / 'include'
        header_parts = header.rsplit(os.sep, 1)

        if len(header_parts) == 1:
            header_parts.insert(0, '')

        common_header = include_path / header
        platform_header = include_path / header_parts[0] / f'_aedi_{state.architecture()}_{header_parts[1]}'
        shutil.move(common_header, platform_header)

        with open(common_header, 'w') as f:
            f.write(f'''
#pragma once

#if defined(__x86_64__)
#   include "_aedi_x86_64_{header_parts[1]}"
#elif defined(__aarch64__)
#   include "_aedi_arm64_{header_parts[1]}"
#else
#   error Unknown architecture
#endif
''')

    def copy_to_bin(self, state: BuildState, filename: str = None, new_filename: str = None):
        bin_path = state.install_path / 'bin'
        os.makedirs(bin_path, exist_ok=True)

        if not filename:
            filename = self.name
        if not new_filename:
            new_filename = filename

        src_path = state.build_path / filename
        dst_path = bin_path / new_filename
        shutil.copy(src_path, dst_path)


class MakeTarget(BuildTarget):
    def __init__(self, name=None):
        super().__init__(name)
        self.tool = 'gmake'

    def configure(self, state: BuildState):
        super().configure(state)

        symlink_directory(state.source, state.build_path)

    def build(self, state: BuildState):
        assert not state.xcode

        args = [
            self.tool,
            '-j', state.jobs,
        ]

        if c_compiler := state.c_compiler():
            args.append(f'CC={c_compiler}')
        if cxx_compiler := state.cxx_compiler():
            args.append(f'CXX={cxx_compiler}')

        args += state.options.to_list()

        work_path = state.build_path / self.src_root
        subprocess.run(args, check=True, cwd=work_path, env=state.environment)


class ConfigureMakeTarget(MakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        super().configure(state)

        work_path = state.build_path / self.src_root
        configure_path = work_path / 'configure'

        common_args = [
            configure_path,
            f'--prefix={state.install_path}',
        ]
        common_args += state.options.to_list()

        disable_dependency_tracking = '--disable-dependency-tracking'
        host = '--host=' + state.host()

        args = copy.copy(common_args)
        args.append(host)
        args.append(disable_dependency_tracking)

        try:
            # Try with host and disabled dependency tracking first
            subprocess.run(args, check=True, cwd=work_path, env=state.environment)
        except subprocess.CalledProcessError:
            # If it fails, try with disabled dependency tracking only
            args = copy.copy(common_args)
            args.append(disable_dependency_tracking)

            try:
                subprocess.run(args, check=True, cwd=work_path, env=state.environment)
            except subprocess.CalledProcessError:
                # Use only common command line arguments
                subprocess.run(common_args, check=True, cwd=work_path, env=state.environment)

    def build(self, state: BuildState):
        # Clear configure script options
        state.options = CommandLineOptions()

        super().build(state)


class CMakeTarget(BuildTarget):
    cached_project_name = None

    def __init__(self, name=None):
        super().__init__(name)

    def detect(self, state: BuildState) -> bool:
        if CMakeTarget.cached_project_name:
            project_name = CMakeTarget.cached_project_name
        else:
            cmakelists_path = state.source / self.src_root / 'CMakeLists.txt'

            if not cmakelists_path.exists():
                return False

            for line in open(cmakelists_path).readlines():
                project_name = CMakeTarget._extract_project_name(line)
                if project_name:
                    project_name = project_name.lower()
                    project_name = project_name.replace(' ', '-')
                    break
            else:
                return False

            if project_name.startswith('lib'):
                project_name = project_name[3:]

            CMakeTarget.cached_project_name = project_name

        return project_name == self.name

    @staticmethod
    def _extract_project_name(line: str):
        project_name = None

        # Try to get project name without whitespaces in it
        match = re.search(r'^\s*project\s*\(\s*(\w[\w-]+)', line, re.IGNORECASE)

        if not match:
            # Try to get project name that contains whitespaces
            match = re.search(r'^\s*project\s*\(\s*"?(\w[\s\w-]+)"?', line, re.IGNORECASE)

        if match:
            project_name = match.group(1)

        return project_name

    def configure(self, state: BuildState):
        super().configure(state)

        args = [
            'cmake',
            '-DCMAKE_BUILD_TYPE=Release',
            f'-DCMAKE_C_FLAGS="-ffile-prefix-map={state.source}/="',
            f'-DCMAKE_CXX_FLAGS="-ffile-prefix-map={state.source}/="',
            f'-DCMAKE_INSTALL_PREFIX={state.install_path}',
            f'-DCMAKE_PREFIX_PATH={state.prefix_path}',
        ]

        if state.xcode:
            args.append('-GXcode')
        else:
            args.append('-GUnix Makefiles')

            if c_compiler := state.c_compiler():
                args.append(f'-DCMAKE_C_COMPILER={c_compiler}')
            if cxx_compiler := state.cxx_compiler():
                args.append(f'-DCMAKE_CXX_COMPILER={cxx_compiler}')

            architecture = state.architecture()
            if architecture != machine():
                args.append('-DCMAKE_SYSTEM_NAME=Darwin')
                args.append('-DCMAKE_SYSTEM_PROCESSOR=' + 'aarch64' if architecture == 'arm64' else architecture)

            sdk_path = state.sdk_path()
            if sdk_path:
                args.append(f'-DCMAKE_OSX_SYSROOT={sdk_path}')

        os_version = state.os_version()
        if os_version:
            args.append('-DCMAKE_OSX_DEPLOYMENT_TARGET=' + str(os_version))

        args += state.options.to_list(CommandLineOptions.CMAKE_RULES)
        args.append(state.source / self.src_root)

        subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)

    def build(self, state: BuildState):
        if state.xcode:
            args = ['cmake', '--open', '.']
        else:
            args = ['gmake', '-j', state.jobs]

            if state.verbose:
                args.append('VERBOSE=1')

        subprocess.run(args, check=True, cwd=state.build_path, env=state.environment)


class ConfigureMakeDependencyTarget(ConfigureMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def post_build(self, state: BuildState):
        self.install(state)


class ConfigureMakeStaticDependencyTarget(ConfigureMakeDependencyTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        state.options['--enable-shared'] = 'no'
        super().configure(state)


class CMakeStaticDependencyTarget(CMakeTarget):
    def __init__(self, name=None):
        super().__init__(name)

    def configure(self, state: BuildState):
        state.options['BUILD_SHARED_LIBS'] = 'NO'
        super().configure(state)

    def post_build(self, state: BuildState):
        self.install(state)

    def keep_module_target(self, state: BuildState, target: str):
        import_patterns = (
            r'list\s*\(APPEND\s+_IMPORT_CHECK_TARGETS\s+(?P<target>\w+::[\w-]+)[\s)]',
            r'list\s*\(APPEND\s+_IMPORT_CHECK_FILES_FOR_(?P<target>\w+::[\w-]+)\s',
        )
        import_regexes = [re.compile(regex, re.IGNORECASE) for regex in import_patterns]

        def _keep_target(line: str):
            for regex in import_regexes:
                match = regex.match(line)

                if match and match.group('target') != target:
                    return None

            return line

        module = 'targets-release.cmake'

        for probe_module in (module, self.name + module):
            module_path = state.install_path / 'lib' / 'cmake' / self.name / probe_module

            if module_path.exists():
                self.update_text_file(module_path, _keep_target)
