
#pragma once

#if defined(__x86_64__)
#   include "_aedi_x86_64_ffi.h"
#elif defined(__aarch64__)
#   include "_aedi_arm64_ffi.h"
#else
#   error Unknown architecture
#endif
