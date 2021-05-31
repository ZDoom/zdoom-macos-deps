#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ZMusic::zmusiclite" for configuration "Release"
set_property(TARGET ZMusic::zmusiclite APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ZMusic::zmusiclite PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libzmusiclite.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS ZMusic::zmusiclite )
list(APPEND _IMPORT_CHECK_FILES_FOR_ZMusic::zmusiclite "${_IMPORT_PREFIX}/lib/libzmusiclite.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
