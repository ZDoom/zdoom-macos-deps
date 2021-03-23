# *ZDoom binary dependencies for macOS

**Dependencies stored in GZDoom repository**

|Name|Links|Homebrew Formula|Repository Path|
|---|---|---|---|
|AsmJit|[Homepage](https://github.com/asmjit/asmjit)||[asmjit](https://github.com/coelckers/gzdoom/tree/master/libraries/asmjit)|
|bzip2|[Homepage](https://www.sourceware.org/bzip2/)|[bzip2.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/bzip2.rb)|[bzip2](https://github.com/coelckers/gzdoom/tree/master/libraries/bzip2)|
|gdtoa|[Homepage](http://www.netlib.org/fp/)||[gdtoa](https://github.com/coelckers/gzdoom/tree/master/libraries/gdtoa)|
|glslang|[Homepage](https://www.khronos.org/opengles/sdk/tools/Reference-Compiler/) / [Download](https://github.com/KhronosGroup/glslang/releases)|[glslang.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/glslang.rb)|[glslang](https://github.com/coelckers/gzdoom/tree/master/libraries/glslang)|
|hqNx|||[hqnx](https://github.com/coelckers/gzdoom/tree/master/src/gamedata/textures/hires/hqnx) / [hqnx_asm](https://github.com/coelckers/gzdoom/tree/master/src/gamedata/textures/hires/hqnx_asm)|
|libjpeg|[Homepage](https://www.ijg.org/)|[jpeg.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/jpeg.rb)|[jpeg](https://github.com/coelckers/gzdoom/tree/master/libraries/jpeg)|
|LZMA|[Homepage](https://www.7-zip.org/sdk.html)||[lzma](https://github.com/coelckers/gzdoom/tree/master/libraries/lzma)|
|volk|[Homepage](https://github.com/zeux/volk)||[volk](https://github.com/coelckers/gzdoom/tree/master/src/rendering/vulkan/thirdparty/volk)|
|Vulkan-Headers|[Homepage](https://github.com/KhronosGroup/Vulkan-Headers)||[vulkan](https://github.com/coelckers/gzdoom/tree/master/src/rendering/vulkan/thirdparty/vulkan)|
|VulkanMemoryAllocator|[Homepage](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator)||[vk_mem_alloc](https://github.com/coelckers/gzdoom/tree/master/src/rendering/vulkan/thirdparty/vk_mem_alloc)|
|xBRZ|[Homepage](https://sourceforge.net/projects/xbrz/)||[xbr](https://github.com/coelckers/gzdoom/tree/master/src/gamedata/textures/hires/xbr)|
|zlib|[Homepage](https://zlib.net/)|[zlib.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/zlib.rb)|[zlib](https://github.com/coelckers/gzdoom/tree/master/libraries/zlib)|

**External dependencies**

|Name|Links|Homebrew Formula|Pulled by|Notes|
|---|---|---|---|---|
|DUMB|[Homepage](http://dumb.sourceforge.net/)|[dumb.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/dumb.rb)|ZMusic||
|FluidSynth|[Homepage](http://www.fluidsynth.org/) / [Download](https://github.com/FluidSynth/fluidsynth/releases)|[fluid-synth.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/fluid-synth.rb)|*ZDoom||
|game-music-emu|[Homepage](https://bitbucket.org/mpyne/game-music-emu/)|[game-music-emu.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/game-music-emu.rb)|ZMusic||
|gettext|[Homepage](https://www.gnu.org/software/gettext/)|[gettext.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/gettext.rb)|GLib|`libintl` only|
|GLib|[Homepage](https://developer.gnome.org/glib/)|[glib.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/glib.rb)|FluidSynth||
|libADLMIDI|[Homepage](https://github.com/Wohlstand/libADLMIDI)||ZMusic||
|libffi|[Homepage](https://sourceware.org/libffi/)|[libffi.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libffi.rb)|GLib|For libinstpatch|
|libFLAC|[Homepage](https://xiph.org/flac/) / [Download](https://github.com/xiph/flac/releases)|[flac.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/flac.rb)|libsndfile||
|libiconv|[Homepage](https://www.gnu.org/software/libiconv/)|[libiconv.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libiconv.rb)|gettext||
|libinstpatch|[Homepage](https://github.com/swami/libinstpatch/)||FluidSynth||
|libjpeg-turbo|[Homepage](https://libjpeg-turbo.org/)|[jpeg-turbo.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/jpeg-turbo.rb)|*ZDoom||
|libogg|[Homepage](https://www.xiph.org/ogg/) / [Download](https://github.com/xiph/ogg/releases)|[libogg.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libogg.rb)|libsndfile||
|libOPNMIDI|[Homepage](https://github.com/Wohlstand/libOPNMIDI/)||ZMusic||
|libsndfile|[Homepage](http://www.mega-nerd.com/libsndfile/) / [Download](https://github.com/erikd/libsndfile/releases)|[libsndfile.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libsndfile.rb)|*ZDoom, FluidSynth||
|libvorbis|[Homepage](https://xiph.org/vorbis/) / [Download](https://github.com/xiph/vorbis/releases)|[libvorbis.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libvorbis.rb)|libsndfile||
|MoltenVK|[Homepage](https://moltengl.com/moltenvk/) / [Download](https://github.com/KhronosGroup/MoltenVK/releases)|[molten-vk.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/molten-vk.rb)|*ZDoom||
|mpg123|[Homepage](https://www.mpg123.de/)|[mpg123.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/mpg123.rb)|*ZDoom||
|OpenAL Soft|[Homepage](https://openal-soft.org/) / [Download](https://github.com/kcat/openal-soft/releases)|[openal-soft.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/openal-soft.rb)|*ZDoom||
|opus|[Homepage](https://www.opus-codec.org/)|[opus.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/opus.rb)|libsndfile||
|PCRE|[Homepage](https://www.pcre.org/)|[pcre.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/pcre.rb)|GLib|For libinstpatch|
|TiMidity|||ZMusic||
|TiMidity++|[Homepage](http://timidity.sourceforge.net/)|[timidity.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/timidity.rb)|ZMusic||
|WildMIDI|[Homepage](https://www.mindwerks.net/projects/wildmidi) / [Download](https://github.com/Mindwerks/wildmidi/releases)||ZMusic||
|zlib-ng|[Homepage](https://github.com/zlib-ng/zlib-ng)|[zlib-ng.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/zlib-ng.rb)|*ZDoom||
|ZMusic|[Homepage](https://github.com/coelckers/ZMusic)||*ZDoom||

Note: OPL implementations used by ZMusic are not listed

**Other dependencies**

|Name|Links|Homebrew Formula|Pulled by|Notes|
|---|---|---|---|---|
|freetype|[Homepage](https://www.freetype.org/)|[freetype.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/freetype.rb)|SDL2_ttf||
|GNU Make|[Homepage](https://www.gnu.org/software/make/)|[make.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/make.rb)|||
|libmikmod|[Homepage](https://mikmod.sourceforge.io/)|[libmikmod.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libmikmod.rb)|SDL2_mixer||
|libsodium|[Homepage](https://libsodium.org/)|[libsodium.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libsodium.rb)|DevilutionX||
|libvpx|[Homepage](https://www.webmproject.org/code/)|[libvpx.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/libvpx.rb)|Raze||
|mad|[Homepage](https://www.underbit.com/products/mad/)|[mad.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/mad.rb)|PrBoom+||
|meson|[Homepage](https://mesonbuild.com/)|[meson.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/meson.rb)|GLib|build only|
|nasm|[Homepage](https://www.nasm.us/)|[nasm.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/nasm.rb)|libFLAC|build only|
|ninja|[Homepage](https://ninja-build.org/)|[ninja.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/ninja.rb)|GLib|build only|
|SDL2|[Homepage](https://www.libsdl.org/)|[sdl2.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/sdl2.rb)|PrBoom+, DevilutionX, *ZDoom SDL backend||
|SDL2_image|[Homepage](https://www.libsdl.org/projects/SDL_image/)|[sdl2_image.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/sdl2_image.rb)|PrBoom+||
|SDL2_mixer|[Homepage](https://www.libsdl.org/projects/SDL_mixer/)|[sdl2_mixer.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/sdl2_mixer.rb)|PrBoom+, DevilutionX||
|SDL2_net|[Homepage](https://www.libsdl.org/projects/SDL_net/)|[sdl2_net.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/sdl2_net.rb)|PrBoom+||
|SDL2_ttf|[Homepage](https://www.libsdl.org/projects/SDL_ttf/)|[sdl2_ttf.rb](https://github.com/Homebrew/homebrew-core/blob/master/Formula/sdl2_ttf.rb)|DevilutionX||
