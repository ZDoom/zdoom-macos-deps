#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "MPG123::libmpg123" for configuration "Release"
set_property(TARGET MPG123::libmpg123 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::libmpg123 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "ASM;C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmpg123.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS MPG123::libmpg123 )
list(APPEND _IMPORT_CHECK_FILES_FOR_MPG123::libmpg123 "${_IMPORT_PREFIX}/lib/libmpg123.a" )

# Import target "MPG123::libout123" for configuration "Release"
set_property(TARGET MPG123::libout123 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::libout123 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libout123.a"
  )


# Import target "MPG123::libsyn123" for configuration "Release"
set_property(TARGET MPG123::libsyn123 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::libsyn123 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsyn123.a"
  )


# Import target "MPG123::mpg123" for configuration "Release"
set_property(TARGET MPG123::mpg123 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::mpg123 PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/mpg123"
  )


# Import target "MPG123::out123" for configuration "Release"
set_property(TARGET MPG123::out123 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::out123 PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/out123"
  )


# Import target "MPG123::mpg123-id3dump" for configuration "Release"
set_property(TARGET MPG123::mpg123-id3dump APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::mpg123-id3dump PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/mpg123-id3dump"
  )


# Import target "MPG123::mpg123-strip" for configuration "Release"
set_property(TARGET MPG123::mpg123-strip APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MPG123::mpg123-strip PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/mpg123-strip"
  )


# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
