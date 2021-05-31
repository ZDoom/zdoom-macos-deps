#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ZMusic::zmusic" for configuration "Release"
set_property(TARGET ZMusic::zmusic APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ZMusic::zmusic PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libzmusic.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS ZMusic::zmusic )
list(APPEND _IMPORT_CHECK_FILES_FOR_ZMusic::zmusic "${_IMPORT_PREFIX}/lib/libzmusic.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
