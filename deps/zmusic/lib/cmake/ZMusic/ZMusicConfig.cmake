
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was ZMusicConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

set(_supported_components "Full;Lite")

if(NOT ZMusic_FIND_COMPONENTS)
	set(ZMusic_FIND_COMPONENTS "${_supported_components}")
endif()

include(CMakeFindDependencyMacro)
foreach(_module ZLIB;SndFile;MPG123)
	find_dependency(${_module})
endforeach()

foreach(_comp ${ZMusic_FIND_COMPONENTS})
	include("${CMAKE_CURRENT_LIST_DIR}/ZMusic${_comp}Targets.cmake")
	set(ZMusic_${_comp}_FOUND TRUE)
endforeach()

check_required_components(ZMusic)
