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

from .library_tier1 import *
from .library_tier2 import *
from .library_tier3 import *
from .main import *
from .special import *
from .tool_tier1 import *
from .tool_tier2 import *


def targets():
    return (
        GZDoomTarget(),
        QZDoomTarget(),
        LZDoomTarget(),
        RazeTarget(),
        HandsOfNecromancyTarget(),
        RedemptionTarget(),
        DisdainTarget(),
        AccTarget(),
        WadExtTarget(),
        ZdbspTarget(),
        ZDRayTarget(),
        PrBoomPlusTarget(),
        DsdaDoom(),
        ChocolateDoomTarget(),
        CrispyDoomTarget(),
        RudeTarget(),
        WoofTarget(),
        DoomRetroTarget(),
        Doom64EXTarget(),
        DevilutionXTarget(),
        EDuke32Target(),
        NBloodTarget(),
        QuakespasmTarget(),
        QuakespasmExpTarget(),

        # Libraries needed for GZDoom and Raze
        Bzip2Target(),
        FfiTarget(),
        FlacTarget(),
        FluidSynthTarget(),
        GlibTarget(),
        IconvTarget(),
        InstPatchTarget(),
        IntlTarget(),
        JpegTurboTarget(),
        LameTarget(),
        MoltenVKTarget(),
        Mpg123Target(),
        OggTarget(),
        OpenALTarget(),
        OpusTarget(),
        PcreTarget(),
        QuasiGlibTarget(),
        SndFileTarget(),
        VorbisTarget(),
        VpxTarget(),
        ZlibNgTarget(),
        ZMusicTarget(),

        # Libraries needed for other targets
        DumbTarget(),
        FmtTarget(),
        MadTarget(),
        MikmodTarget(),
        ModPlugTarget(),
        OpusFileTarget(),
        PngTarget(),
        PortMidiTarget(),
        SamplerateTarget(),
        Sdl2Target(),
        Sdl2ImageTarget(),
        Sdl2MixerTarget(),
        Sdl2NetTarget(),
        SodiumTarget(),
        VulkanHeadersTarget(),
        VulkanLoaderTarget(),
        XmpTarget(),

        # Obsolete libraries without binaries
        BrotliTarget(),
        ExpatTarget(),
        FreeImageTarget(),
        FreeTypeTarget(),
        FtglTarget(),
        GlewTarget(),
        HarfBuzzTarget(),
        LuaTarget(),
        LzmaTarget(),
        Sdl2TtfTarget(),
        SfmlTarget(),
        TiffTarget(),
        WebpTarget(),
        WxWidgetsTarget(),
        ZstdTarget(),

        # Tools needed to build main targets and libraries (tiers 1 and 2)
        BuildCMakeTarget(),
        GmakeTarget(),
        MesonTarget(),
        NasmTarget(),
        NinjaTarget(),
        PkgConfigTarget(),
        YasmTarget(),

        # Tools without binaries stored in the repo, can be outdated
        P7ZipTarget(),
        PbzxTarget(),
        UnrarTarget(),
        ZipTarget(),

        # Special
        BuildPrefix(),
        CleanAllTarget(),
        CleanDepsTarget(),
        DownloadCMakeTarget(),
        TestDepsTarget(),
    )
