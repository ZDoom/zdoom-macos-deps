#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "SampleRate::samplerate" for configuration "Release"
set_property(TARGET SampleRate::samplerate APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(SampleRate::samplerate PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsamplerate.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS SampleRate::samplerate )
list(APPEND _IMPORT_CHECK_FILES_FOR_SampleRate::samplerate "${_IMPORT_PREFIX}/lib/libsamplerate.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
