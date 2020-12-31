
#pragma once

#if defined(__x86_64__)
#   include "x86_64/SDL_config.h"
#elif defined(__aarch64__)
#   include "arm64/SDL_config.h"
#else
#   error Unknown architecture
#endif
