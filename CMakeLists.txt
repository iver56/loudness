cmake_minimum_required(VERSION 3.22)
project(loudness LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

file(GLOB_RECURSE LIBLOUDNESS_SOURCES CONFIGURE_DEPENDS
     "src/loudness/*.cpp")

add_library(libloudness STATIC ${LIBLOUDNESS_SOURCES})

target_include_directories(libloudness PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor/gcem/include
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor/thread-pool/include
)

target_compile_definitions(libloudness PRIVATE GCEM_USE_STD_MATH_FUNCTIONS)

pybind11_add_module(loudness src/loudness.cpp)
target_link_libraries(loudness PRIVATE libloudness)

include(GNUInstallDirs)
if(NOT DEFINED SKBUILD_PLATLIB_DIR)
    set(SKBUILD_PLATLIB_DIR "${CMAKE_INSTALL_LIBDIR}")
endif()

install(
    TARGETS loudness
    LIBRARY DESTINATION "${SKBUILD_PLATLIB_DIR}"
    RUNTIME DESTINATION "${SKBUILD_PLATLIB_DIR}"
)
