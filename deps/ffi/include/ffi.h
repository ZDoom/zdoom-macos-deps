
#pragma once

#if defined(__x86_64__)
#   include "x86_64/ffi.h"
#elif defined(__aarch64__)
#   include "arm64/ffi.h"
#else
#   error Unknown architecture
#endif
