# *ZDoom binary dependencies for macOS

This repository contains all binary dependencies required to build macOS application bundles of [ZDoom-derived](https://zdoom.org) source ports. A few other projects are supported as well, with lesser priority though.

## Usage

Download source code, and build a target

```sh
build.py --target=<target-name>
```

Build target from existing source code

```sh
build.py --source=<path-to-source-code>
```

Generate Xcode project instead of building target, and open it

```sh
build.py --source=...|--target=... --xcode
```

Run `build.py` without arguments for complete list of options.

## Prerequisites

* Xcode 12.2 or newer, launch it once to finish installation
* CMake 3.18 or newer, `CMake.app` in `/Applications` or system-wide `cmake` console executable

## Common information

Libraries were built using 10.9 SDK (Intel x64_64) and 11.0 SDK (ARM64).  
macOS 10.9 SDK was obtained from Xcode 6.4. macOS 11.0 SDK was obtained from Xcode 12.2.
