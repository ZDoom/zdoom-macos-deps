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

import glob
import os
import shutil
from pathlib import Path

from ..state import BuildState
from . import base


class BrotliTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='brotli'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/google/brotli/archive/refs/tags/v1.0.9.tar.gz',
            'f9e8d81d0405ba66d181529af42a3354f838c939095ff99930da6aa9cdf6fe46')

    def post_build(self, state: BuildState):
        super().post_build(state)

        dylib_pattern = str(state.install_path / 'lib/*.dylib')
        for dylib in glob.iglob(dylib_pattern):
            os.unlink(dylib)

        archive_suffix = '-static.a'
        archive_pattern = str(state.install_path / f'lib/*{archive_suffix}')
        for archive in glob.iglob(archive_pattern):
            no_suffix_name = archive.replace(archive_suffix, '.a')
            os.rename(archive, no_suffix_name)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        return line.replace('-R${libdir} ', '') if line.startswith('Libs:') else line


class ExpatTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='expat'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libexpat/libexpat/releases/download/R_2_4_1/expat-2.4.1.tar.xz',
            'cf032d0dba9b928636548e32b327a2d66b1aab63c4f4a13dd132c2d1d2f2fb6a')

    def configure(self, state: BuildState):
        opts = state.options
        opts['EXPAT_BUILD_EXAMPLES'] = 'NO'
        opts['EXPAT_BUILD_TESTS'] = 'NO'
        opts['EXPAT_BUILD_TOOLS'] = 'NO'

        super().configure(state)


class FftwTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='fftw'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://fftw.org/fftw-3.3.10.tar.gz',
            '56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467')

    def configure(self, state: BuildState):
        opts = state.options
        opts['BUILD_TESTS'] = 'NO'
        opts['DISABLE_FORTRAN'] = 'YES'
        opts['ENABLE_THREADS'] = 'YES'

        if state.architecture() == 'x86_64':
            opts['ENABLE_SSE2'] = 'YES'
            opts['ENABLE_AVX'] = 'YES'
            opts['ENABLE_AVX2'] = 'YES'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_dirs(line: str):
            if line.startswith('set (FFTW3_INCLUDE_DIRS '):
                return 'set (FFTW3_INCLUDE_DIRS "${CMAKE_CURRENT_LIST_DIR}/../../../include")\n'
            elif line.startswith('set (FFTW3_LIBRARY_DIRS '):
                return 'set (FFTW3_LIBRARY_DIRS "${CMAKE_CURRENT_LIST_DIR}/../../")\n'

            return line

        cmake_module = state.install_path / 'lib/cmake/fftw3/FFTW3Config.cmake'
        self.update_text_file(cmake_module, update_dirs)


class FreeImageTarget(base.MakeTarget):
    def __init__(self, name='freeimage'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/freeimage/Source%20Distribution/3.18.0/FreeImage3180.zip',
            'f41379682f9ada94ea7b34fe86bf9ee00935a3147be41b6569c9605a53e438fd',
            patches='freeimage-fix-arm64')

    HEADER_FILE = 'Source/FreeImage.h'

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file(self.HEADER_FILE)

    def configure(self, state: BuildState):
        super().configure(state)

        # These flags are copied from Makefile.gnu
        common_flags = ' -O3 -fPIC -fexceptions -fvisibility=hidden'

        env = state.environment
        env['CFLAGS'] += common_flags + ' -std=gnu89 -Wno-implicit-function-declaration'
        env['CXXFLAGS'] += common_flags + ' -Wno-ctor-dtor-privacy'

        for option in ('-f', 'Makefile.gnu', 'libfreeimage.a'):
            state.options[option] = None

    def post_build(self, state: BuildState):
        include_path = state.install_path / 'include'
        os.makedirs(include_path, exist_ok=True)
        shutil.copy(state.build_path / self.HEADER_FILE, include_path)

        lib_path = state.install_path / 'lib'
        os.makedirs(lib_path, exist_ok=True)
        shutil.copy(state.build_path / 'libfreeimage.a', lib_path)

        self.write_pc_file(state, version='3.18.0', libs='-lfreeimage -lc++')


class FreeTypeTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='freetype'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/freetype/freetype2/2.13.2/freetype-2.13.2.tar.xz',
            '12991c4e55c506dd7f9b765933e62fd2be2e06d421505d7950a132e4f1bb484d')

    def post_build(self, state: BuildState):
        super().post_build(state)

        bin_path = state.install_path / 'bin'
        os.makedirs(bin_path)
        shutil.copy(state.patch_path / 'freetype-config', bin_path)

        def update_linker_flags(line: str):
            link_flags = '-lbz2 -lpng16 -lz'
            link_var = '  INTERFACE_LINK_LIBRARIES '

            return f'{link_var}"{link_flags}"\n' if line.startswith(link_var) else line

        cmake_module = state.install_path / 'lib/cmake/freetype/freetype-config.cmake'
        self.update_text_file(cmake_module, update_linker_flags)


class FtglTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='ftgl'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://downloads.sourceforge.net/project/ftgl/FTGL%20Source/2.1.3~rc5/ftgl-2.1.3-rc5.tar.gz',
            '5458d62122454869572d39f8aa85745fc05d5518001bcefa63bd6cbb8d26565b',
            patches='ftgl-support-arm64')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('ftgl.pc.in')

    def configure(self, state: BuildState):
        opts = state.options
        opts['--with-glut-inc'] = '/dev/null'
        opts['--with-glut-lib'] = '/dev/null'

        super().configure(state)


class GlewTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='glew'):
        super().__init__(name)
        self.src_root = 'build/cmake'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/nigels-com/glew/releases/download/glew-2.2.0/glew-2.2.0.tgz',
            'd4fc82893cfb00109578d0a1a2337fb8ca335b3ceccf97b97e5cc7f08e4353e1')

    def configure(self, state: BuildState):
        state.options['BUILD_UTILS'] = 'NO'
        super().configure(state)

    LINKER_FLAGS = '-framework OpenGL'

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_linker_flags(line: str):
            link_var = '  INTERFACE_LINK_LIBRARIES '

            if line.startswith(link_var):
                return f'{link_var}"{GlewTarget.LINKER_FLAGS}"\n'

            return line

        cmake_module = state.install_path / 'lib/cmake/glew/glew-targets.cmake'
        self.update_text_file(cmake_module, update_linker_flags)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        libs = 'Libs:'

        if line.startswith(libs):
            return libs + ' -L${libdir} -lGLEW ' + GlewTarget.LINKER_FLAGS + os.linesep

        return line


class HarfBuzzTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='harfbuzz'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/harfbuzz/harfbuzz/archive/refs/tags/2.8.2.tar.gz',
            '4164f68103e7b52757a732227cfa2a16cfa9984da513843bb4eb7669adc6f220')

    def configure(self, state: BuildState):
        state.options['HB_HAVE_FREETYPE'] = 'ON'
        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        def update_config_cmake(line: str):
            include_var = '  INTERFACE_INCLUDE_DIRECTORIES '
            link_var = '  INTERFACE_LINK_LIBRARIES '

            if line.startswith(include_var):
                return include_var + '"${_IMPORT_PREFIX}/include/harfbuzz"\n'
            elif line.startswith(link_var):
                return link_var + '"-framework ApplicationServices"\n'

            return line

        config_path = state.install_path / 'lib/cmake/harfbuzz/harfbuzzConfig.cmake'
        self.update_text_file(config_path, update_config_cmake)

        self.write_pc_file(state, description='HarfBuzz text shaping library', version='2.8.2', libs='-lharfbuzz',
                           libs_private='-lc++ -framework CoreFoundation -framework CoreGraphics -framework CoreText')


class HighwayTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='highway'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/google/highway/archive/refs/tags/1.0.6.tar.gz',
            'd89664a045a41d822146e787bceeefbf648cc228ce354f347b18f2b419e57207')

    def configure(self, state: BuildState):
        opts = state.options
        opts['HWY_ENABLE_CONTRIB'] = 'NO'
        opts['HWY_ENABLE_EXAMPLES'] = 'NO'
        opts['HWY_ENABLE_TESTS'] = 'NO'

        super().configure(state)


class JpegTurboTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='jpeg-turbo'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.1.0/libjpeg-turbo-3.1.0.tar.gz',
            '9564c72b1dfd1d6fe6274c5f95a8d989b59854575d4bbee44ade7bc17aa9bc93')

    def configure(self, state: BuildState):
        state.options['ENABLE_SHARED'] = 'NO'
        super().configure(state)


class LuaTarget(base.MakeTarget):
    def __init__(self, name='lua'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.lua.org/ftp/lua-5.4.7.tar.gz',
            '9fbf5e28ef86c69858f6d3d34eccc32e911c1a28b4120ff3e84aaa70cfbf1e30')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('src/lua.h')

    def post_build(self, state: BuildState):
        opts = state.options
        opts['install'] = None
        opts['INSTALL_TOP'] = state.install_path

        self.install(state, state.options)


class Sdl2TtfTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='sdl2_ttf'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.15.tar.gz',
            'a9eceb1ad88c1f1545cd7bd28e7cbc0b2c14191d40238f531a15b01b1b22cd33',
            patches='sdl2_ttf-fix-cmake')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('SDL2_ttf.pc.in')

    def configure(self, state: BuildState):
        state.options['VERSION'] = '2.0.15'
        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)
        shutil.move(state.install_path / 'SDL2_ttf.framework/Resources', state.install_path / 'lib/cmake/SDL2_ttf')

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        return line + 'Requires.private: freetype2\n' if line.startswith('Requires:') else line


class SfmlTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='sfml'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://www.sfml-dev.org/files/SFML-2.5.1-sources.zip',
            'bf1e0643acb92369b24572b703473af60bac82caf5af61e77c063b779471bb7f',
            patches='sfml-support-arm64')

    def configure(self, state: BuildState):
        opts = state.options
        opts['CMAKE_OSX_ARCHITECTURES'] = state.architecture()
        opts['SFML_USE_SYSTEM_DEPS'] = 'YES'
        opts['SFML_MISC_INSTALL_PREFIX'] = state.install_path / 'share/SFML'
        # Use OpenAL Soft instead of Apple's framework
        opts['OPENAL_INCLUDE_DIR'] = state.include_path / 'AL'
        opts['OPENAL_LIBRARY'] = state.lib_path / 'libopenal.a'

        super().configure(state)


class TiffTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='tiff'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://download.osgeo.org/libtiff/tiff-4.3.0.tar.gz',
            '0e46e5acb087ce7d1ac53cf4f56a09b221537fc86dfc5daaad1c2e89e1b37ac8',
            patches='tiff-remove-useless')

    def configure(self, state: BuildState):
        opts = state.options
        opts['cxx'] = 'NO'
        opts['lzma'] = 'YES'

        super().configure(state)

    @staticmethod
    def _process_pkg_config(pcfile: Path, line: str) -> str:
        version = 'Version:'
        cflags = 'Cflags:'
        libs = 'Libs:'

        if line.startswith(version):
            return version + ' 4.3.0\n'
        elif line.startswith(cflags):
            return cflags + ' -I${includedir}\nRequires.private: libjpeg liblzma libwebp libzstd zlib\n'
        elif line.startswith(libs):
            return libs + ' -L${libdir} -ltiff\n'

        return line


class UsbTarget(base.ConfigureMakeStaticDependencyTarget):
    def __init__(self, name='usb'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/libusb/libusb/releases/download/v1.0.27/libusb-1.0.27.tar.bz2',
            'ffaa41d741a8a3bee244ac8e54a72ea05bf2879663c098c82fc5757853441575')

    def detect(self, state: BuildState) -> bool:
        return state.has_source_file('libusb/libusb.h')


class WxWidgetsTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='wxwidgets'):
        super().__init__(name)

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/wxWidgets/wxWidgets/releases/download/v3.1.5/wxWidgets-3.1.5.tar.bz2',
            'd7b3666de33aa5c10ea41bb9405c40326e1aeb74ee725bb88f90f1d50270a224',
            patches='wxwidgets-library-suffix')

    def configure(self, state: BuildState):
        opts = state.options
        opts['wxBUILD_SHARED'] = 'NO'
        opts['wxUSE_LIBLZMA'] = 'YES'
        opts['wxUSE_LIBSDL'] = 'NO'
        opts['wxUSE_LIBJPEG'] = 'sys'
        opts['wxUSE_LIBPNG'] = 'sys'
        opts['wxUSE_LIBTIFF'] = 'sys'

        super().configure(state)

    def post_build(self, state: BuildState):
        super().post_build(state)

        # Replace prefix in setup.h
        def patch_setup_h(line: str):
            prefix = '#define wxINSTALL_PREFIX '
            return f'{prefix}"/usr/local"\n' if line.startswith(prefix) else line

        setup_h_path = state.install_path / 'lib/wx/include/osx_cocoa-unicode-static-3.1/wx/setup.h'
        self.update_text_file(setup_h_path, patch_setup_h)

        # Fix a few wx-config entries
        def patch_wx_config(line: str):
            prefix = 'prefix=${input_option_prefix-${this_prefix:-'
            is_cross_func = 'is_cross() '
            is_cross_test = 'is_cross && target='
            output_option_cc = '[ -z "$output_option_cc" '
            output_option_cxx = '[ -z "$output_option_cxx" '
            output_option_ld = '[ -z "$output_option_ld" '
            ldlibs_gl = 'ldlibs_gl='

            if line.startswith(prefix):
                return prefix + '$(cd "${0%/*}/.."; pwd)}}\n'
            elif line.startswith(is_cross_func):
                return is_cross_func + '{ false; }\n'
            elif line.startswith(is_cross_test):
                return is_cross_test + '""\n'
            elif line.startswith(output_option_cc):
                return output_option_cc + '] || echo "gcc"\n'
            elif line.startswith(output_option_cxx):
                return output_option_cxx + '] || echo "g++"\n'
            elif line.startswith(output_option_ld):
                return output_option_ld + '] || echo "g++ -o"\n'
            elif line.startswith(ldlibs_gl):
                return ldlibs_gl + '"-lwx_baseu-3.1 -lwx_osx_cocoau_core-3.1 -framework OpenGL"\n'

            return line

        wx_config_path = state.install_path / 'bin/wx-config'
        self.update_text_file(wx_config_path, patch_wx_config)


class ZstdTarget(base.CMakeStaticDependencyTarget):
    def __init__(self, name='zstd'):
        super().__init__(name)
        self.src_root = 'build/cmake'

    def prepare_source(self, state: BuildState):
        state.download_source(
            'https://github.com/facebook/zstd/releases/download/v1.5.0/zstd-1.5.0.tar.gz',
            '5194fbfa781fcf45b98c5e849651aa7b3b0a008c6b72d4a0db760f3002291e94')

    def configure(self, state: BuildState):
        opts = state.options
        opts['ZSTD_BUILD_PROGRAMS'] = 'NO'
        opts['ZSTD_BUILD_SHARED'] = 'NO'

        super().configure(state)
