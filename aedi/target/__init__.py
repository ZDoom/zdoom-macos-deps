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

from .dependency import *
from .main import *
from .special import *


def targets():
    return (
        GZDoomTarget(),
        QZDoomTarget(),
        LZDoomTarget(),
        LZDoom3Target(),
        RazeTarget(),
        AccTarget(),
        PrBoomPlusTarget(),
        ChocolateDoomTarget(),
        CrispyDoomTarget(),
        RudeTarget(),
        WoofTarget(),
        DoomRetroTarget(),
        Doom64EXTarget(),
        DevilutionXTarget(),
        DevilutionXHellfireTarget(),
        EDuke32Target(),
        NBloodTarget(),
        QuakespasmTarget(),

        # Dependencies
        Bzip2Target(),
        DumbTarget(),
        FfiTarget(),
        FlacTarget(),
        FluidSynthTarget(),
        FreetypeTarget(),
        GlibTarget(),
        GmakeTarget(),
        IconvTarget(),
        InstPatchTarget(),
        IntlTarget(),
        JpegTurboTarget(),
        MadTarget(),
        MesonTarget(),
        MikmodTarget(),
        ModPlugTarget(),
        MoltenVKTarget(),
        Mpg123Target(),
        NasmTarget(),
        NinjaTarget(),
        OggTarget(),
        OpenALTarget(),
        OpusTarget(),
        OpusFileTarget(),
        PcreTarget(),
        PkgConfigTarget(),
        PngTarget(),
        PortMidiTarget(),
        SamplerateTarget(),
        Sdl2Target(),
        Sdl2ImageTarget(),
        Sdl2MixerTarget(),
        Sdl2NetTarget(),
        Sdl2TtfTarget(),
        SndFileTarget(),
        SodiumTarget(),
        VorbisTarget(),
        VpxTarget(),
        WebpTarget(),
        YasmTarget(),
        ZlibTarget(),
        ZMusicTarget(),

        # Special
        CleanAllTarget(),
        CleanDepsTarget(),
        TestDepsTarget(),
    )
