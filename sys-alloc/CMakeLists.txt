cmake_minimum_required(VERSION 3.10)
project(sys_alloc_vnp C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/W4 /WX /D_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -Werror -O3 -fPIC -D_GNU_SOURCE)
endif()

add_library(sys_alloc SHARED allocator.c)

if(UNIX AND NOT APPLE)
    target_link_libraries(sys_alloc pthread rt)
endif()
