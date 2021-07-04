
#pragma once

#if defined(__x86_64__)
#   include "_aedi_x86_64_glibconfig.h"
#elif defined(__aarch64__)
#   include "_aedi_arm64_glibconfig.h"
#else
#   error Unknown architecture
#endif
