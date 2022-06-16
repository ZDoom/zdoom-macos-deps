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

from .base import *


class WxWidgetsTarget(CMakeStaticDependencyTarget):
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
