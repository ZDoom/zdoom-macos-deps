## ZDoom / GZDoom / QZDoom dependencies for macOS

Dependencies to build [ZDoom](http://zdoom.org) / [GZDoom](http://gzdoom.drdteam.org/) / [QZDoom](http://qzdoom.drdteam.org/) binaries for macOS

Libraries were built with the following environment variables set:
```sh
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export  LDFLAGS="-L/usr/local/lib     -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
```
OS X 10.9 SDK was obtained from Xcode 6.4 which is the last version with Mavericks support.

The exception is MoltenVK as it must be build as a dynamic library and requires 10.11 or newer.  
In addition to CMake, it needs Python 3.x to build its dependencies.
```sh
# Assumes CMake and Python 3 are accessible
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export  LDFLAGS="-L/usr/local/lib     -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"

git clone https://github.com/KhronosGroup/MoltenVK.git

cd MoltenVK
git checkout v1.0.38  # See https://github.com/KhronosGroup/MoltenVK/tags

./fetchDependencies -v
xcodebuild -project MoltenVK/MoltenVK.xcodeproj -scheme MoltenVK-macOS
```
