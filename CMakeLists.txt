cmake_minimum_required(VERSION 3.24)
project(fs1 C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

find_package(SDL3 REQUIRED CONFIG)

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
