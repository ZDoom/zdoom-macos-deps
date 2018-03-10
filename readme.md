## ZDoom / GZDoom / QZDoom dependencies for macOS

Dependencies to build [ZDoom](http://zdoom.org) / [GZDoom](http://gzdoom.drdteam.org/) / [QZDoom](http://qzdoom.drdteam.org/) binaries for macOS

Libraries were built with the following environment variables set:
```
export   CFLAGS="-I/usr/local/include -mmacosx-version-min=10.7 -isysroot MacOSX10.7.sdk"
export CXXFLAGS="-I/usr/local/include -mmacosx-version-min=10.7 -isysroot MacOSX10.7.sdk"
export CPPFLAGS="-I/usr/local/include -mmacosx-version-min=10.7 -isysroot MacOSX10.7.sdk"
export  LDFLAGS="-L/usr/local/lib -mmacosx-version-min=10.7 -isysroot MacOSX10.7.sdk"
```
Mac OS X 10.7 SDK was obtained from Xcode 4.6.3 which is the last version with Lion support.
