import os
import sys
import argparse


def create_cpp_cmake_project(project_name, target_dir):
    """Create a C++ project with CMake build system."""
    project_path = os.path.join(target_dir, project_name)
    src_path = os.path.join(project_path, "src")
    include_path = os.path.join(project_path, "include")
    tests_path = os.path.join(project_path, "tests")
    build_path = os.path.join(project_path, "build")

    for path in [project_path, src_path, include_path, tests_path, build_path]:
        os.makedirs(path, exist_ok=True)

    # CMakeLists.txt (root)
    cmake_content = f"""cmake_minimum_required(VERSION 3.16)
project({project_name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Include directories
include_directories(include)

# Collect source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Main executable
add_executable({project_name} ${{SOURCES}})

# Optional: enable testing
enable_testing()
add_subdirectory(tests)
"""
    with open(os.path.join(project_path, "CMakeLists.txt"), "w") as f:
        f.write(cmake_content)

    # tests/CMakeLists.txt
    tests_cmake = f"""# Add test executable
file(GLOB TEST_SOURCES "*.cpp")
if(TEST_SOURCES)
    add_executable({project_name}_tests ${{TEST_SOURCES}})
    target_include_directories({project_name}_tests PRIVATE ${{CMAKE_SOURCE_DIR}}/include)
    add_test(NAME {project_name}_tests COMMAND {project_name}_tests)
endif()
"""
    with open(os.path.join(tests_path, "CMakeLists.txt"), "w") as f:
        f.write(tests_cmake)

    # include/app.h
    header_content = f"""#pragma once

#include <string>

namespace {project_name.replace('-', '_')} {{

/**
 * @brief Returns a greeting message.
 * @param name The name to greet.
 * @return Greeting string.
 */
std::string greet(const std::string& name);

}} // namespace {project_name.replace('-', '_')}
"""
    with open(os.path.join(include_path, "app.h"), "w") as f:
        f.write(header_content)

    # src/app.cpp
    app_cpp = f"""#include "app.h"

namespace {project_name.replace('-', '_')} {{

std::string greet(const std::string& name) {{
    return "Hello, " + name + "!";
}}

}} // namespace {project_name.replace('-', '_')}
"""
    with open(os.path.join(src_path, "app.cpp"), "w") as f:
        f.write(app_cpp)

    # src/main.cpp
    main_cpp = f"""#include <iostream>
#include "app.h"

int main(int argc, char* argv[]) {{
    std::string name = (argc > 1) ? argv[1] : "World";
    std::cout << {project_name.replace('-', '_')}::greet(name) << std::endl;
    return 0;
}}
"""
    with open(os.path.join(src_path, "main.cpp"), "w") as f:
        f.write(main_cpp)

    # tests/test_main.cpp — minimal test without external framework
    test_cpp = f"""#include <iostream>
#include <cassert>
#include <string>
#include "app.h"

void test_greet_world() {{
    std::string result = {project_name.replace('-', '_')}::greet("World");
    assert(result == "Hello, World!" && "greet('World') should return 'Hello, World!'");
    std::cout << "[PASS] test_greet_world" << std::endl;
}}

void test_greet_custom_name() {{
    std::string result = {project_name.replace('-', '_')}::greet("Claude");
    assert(result == "Hello, Claude!" && "greet('Claude') should return 'Hello, Claude!'");
    std::cout << "[PASS] test_greet_custom_name" << std::endl;
}}

int main() {{
    test_greet_world();
    test_greet_custom_name();
    std::cout << "All tests passed!" << std::endl;
    return 0;
}}
"""
    with open(os.path.join(tests_path, "test_main.cpp"), "w") as f:
        f.write(test_cpp)

    # .gitignore
    gitignore = """build/
*.o
*.a
*.so
*.dll
*.exe
.cache/
compile_commands.json
CMakeFiles/
CMakeCache.txt
cmake_install.cmake
"""
    with open(os.path.join(project_path, ".gitignore"), "w") as f:
        f.write(gitignore)

    # README.md
    readme = f"""# {project_name}

A C++17 project built with CMake.

## Prerequisites

- CMake 3.16+
- A C++17-compatible compiler (GCC 9+, Clang 10+, MSVC 2019+)

## Build

```bash
cmake -S . -B build
cmake --build build
```

## Run

```bash
./build/{project_name}          # Linux/macOS
.\\build\\Debug\\{project_name}.exe  # Windows
```

## Test

```bash
cd build && ctest --output-on-failure
```

## Project Structure

```
{project_name}/
├── CMakeLists.txt      # Root build configuration
├── include/
│   └── app.h           # Public headers
├── src/
│   ├── main.cpp        # Entry point
│   └── app.cpp         # Implementation
├── tests/
│   ├── CMakeLists.txt  # Test build configuration
│   └── test_main.cpp   # Unit tests
└── build/              # Build output (git-ignored)
```
"""
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme)

    print(f"C++ CMake project '{project_name}' created at {project_path}")


def create_cpp_console_project(project_name, target_dir):
    """Create a minimal single-file C++ console application."""
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # main.cpp
    main_cpp = f"""#include <iostream>
#include <string>

int main(int argc, char* argv[]) {{
    std::string name = (argc > 1) ? argv[1] : "World";
    std::cout << "Hello, " << name << "!" << std::endl;
    return 0;
}}
"""
    with open(os.path.join(project_path, "main.cpp"), "w") as f:
        f.write(main_cpp)

    # Simple CMakeLists.txt
    cmake_content = f"""cmake_minimum_required(VERSION 3.16)
project({project_name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable({project_name} main.cpp)
"""
    with open(os.path.join(project_path, "CMakeLists.txt"), "w") as f:
        f.write(cmake_content)

    # .gitignore
    gitignore = "build/\n*.o\n*.exe\n*.out\n"
    with open(os.path.join(project_path, ".gitignore"), "w") as f:
        f.write(gitignore)

    # README.md
    readme = f"""# {project_name}

A minimal C++17 console application.

## Build with CMake

```bash
cmake -S . -B build
cmake --build build
./build/{project_name}
```

## Build manually (GCC/Clang)

```bash
g++ -std=c++17 -o {project_name} main.cpp
./{project_name}
```
"""
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme)

    print(f"C++ console project '{project_name}' created at {project_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a C++ project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument(
        "--type",
        choices=["cmake", "console"],
        default="cmake",
        help="Project type: cmake (full CMake project) or console (single-file)",
    )
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    if args.type == "console":
        create_cpp_console_project(args.project_name, args.target_dir)
    else:
        create_cpp_cmake_project(args.project_name, args.target_dir)
