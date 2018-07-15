## ZDoom / GZDoom / QZDoom dependencies for macOS

Dependencies to build [ZDoom](http://zdoom.org) / [GZDoom](http://gzdoom.drdteam.org/) / [QZDoom](http://qzdoom.drdteam.org/) binaries for macOS

Libraries were built with the following environment variables set:
```
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
export  LDFLAGS="-L/usr/local/lib     -mmacosx-version-min=10.9 -isysroot MacOSX10.9.sdk"
```
OS X 10.9 SDK was obtained from Xcode 6.4 which is the last version with Mavericks support.
