# *ZDoom binary dependencies for macOS

This repository contains all binary dependencies required to build macOS application bundles of [ZDoom-derived](https://zdoom.org) source ports.

Libraries were built with the following environment variables set:
```sh
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export  LDFLAGS="-L/usr/local/lib     -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
```
macOS 10.9 SDK was obtained from Xcode 6.4 which is the last version shipped with Mavericks SDK.

The exception is MoltenVK as it must be build as a dynamic library and requires 10.11 or newer.  
In addition to CMake, it needs Python 3.x to build its dependencies.
```sh
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"
export  LDFLAGS="-L/usr/local/lib     -mmacosx-version-min=10.11 -isysroot MacOSX10.11.sdk"

git clone https://github.com/KhronosGroup/MoltenVK.git

cd MoltenVK
git checkout v1.0.38  # See https://github.com/KhronosGroup/MoltenVK/tags

./fetchDependencies -v  # Assumes CMake and Python 3 are accessible
xcodebuild -project MoltenVK/MoltenVK.xcodeproj -scheme MoltenVK-macOS
```
macOS 10.11 SDK was obtained from Xcode 7.3.1 which is the last version shipped with El Capitan SDK.
