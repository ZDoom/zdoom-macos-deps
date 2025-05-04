# *ZDoom binary dependencies for macOS

This repository contains all binary dependencies required to build macOS application bundles of [ZDoom-derived](https://zdoom.org) source ports.

[![Build Targets](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/build.yml/badge.svg)](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/build.yml)
[![Lint Code](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/lint.yml/badge.svg)](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/lint.yml)
[![Test Libraries](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/test.yml/badge.svg)](https://github.com/ZDoom/zdoom-macos-deps/actions/workflows/test.yml)

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

Xcode 12.2 or newer is required in order to build universal binaries. Launch Xcode once to finish its installation. In theory, it is possible to use older versions of Xcode to build Intel target only by adding `--disable-arm` command line option.

## Directories

* `build` directory stores all intermediary files created during targets compilation, customizable with `--build-path` command line option
* `deps` directory stores all dependencies (headers, libraries, executable and additional files) in the corresponding subdirectories
* `output` directory stores built main targets, customizable with `--output-path` command line option
* `prefix` directory stores symbolic links to all dependencies combined as one build root
* `sdk` directory can contain macOS SDKs that will be picked if match with macOS deployment versions
* `source` directory stores targets source code, customizable with `--source-path` command line option
* `temp` directory stores temporary files, customizable with `--temp-path` command line option
