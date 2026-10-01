cmake_minimum_required(VERSION 3.24)
project(fs1 C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Use an installed SDL3 (3.4 or newer) if there is one; otherwise download and build it,
# which is what headless Linux machines without SDL3 packages need.
find_package(SDL3 3.4 CONFIG QUIET)
if(NOT SDL3_FOUND)
    message(STATUS "SDL3 not found: fetching and building it")
    include(FetchContent)
    set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
    set(SDL_TESTS OFF CACHE BOOL "" FORCE)
    set(SDL_EXAMPLES OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(SDL3
        GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
        GIT_TAG release-3.4.0
        GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(SDL3)
endif()

add_executable(fs1
    src/main.c
    src/disk.c
    src/cpu8086.c
    src/pc.c
    src/native.c
)
target_link_libraries(fs1 PRIVATE SDL3::SDL3)

if(MSVC)
    target_compile_options(fs1 PRIVATE /W4)
else()
    target_compile_options(fs1 PRIVATE -Wall -Wextra)
endif()
