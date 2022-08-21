#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "SDL2_net::SDL2_net-static" for configuration "Release"
set_property(TARGET SDL2_net::SDL2_net-static APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(SDL2_net::SDL2_net-static PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libSDL2_net.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS SDL2_net::SDL2_net-static )
list(APPEND _IMPORT_CHECK_FILES_FOR_SDL2_net::SDL2_net-static "${_IMPORT_PREFIX}/lib/libSDL2_net.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
