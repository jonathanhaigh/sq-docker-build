#!/usr/bin/env python3

import argparse
import json
import logging
import os
import pathlib
import subprocess

def env_var_to_bool(value):
    return value.upper() not in ("0", "FALSE", "NO", "")

def get_arg_from_env(args, var, typ):
    for env_var in (var.upper(), f"SQ_{var.upper()}"):
        if env_var in os.environ:
            args[var] = typ(os.environ[env_var])


def get_default_args():
    return {
        "build_dir": pathlib.Path("build"),
        "build_type": "Release",
        "clang_tidy": False,
        "coverage": False,
        "cxx_compiler": "clang++",
        "jobs": 4,
        "repo": pathlib.Path("/work"),
        "test": False,
    }

def parse_env():
    args = {}

    if "GITHUB_WORKSPACE" in os.environ:
        args["repo"] = pathlib.Path(os.environ["GITHUB_WORKSPACE"])

    get_arg_from_env(args, "build_dir", pathlib.Path)
    get_arg_from_env(args, "build_type", str)
    get_arg_from_env(args, "clang_tidy", env_var_to_bool)
    get_arg_from_env(args, "coverage", env_var_to_bool)
    get_arg_from_env(args, "cxx_compiler", str)
    get_arg_from_env(args, "jobs", int)
    get_arg_from_env(args, "repo", pathlib.Path)
    get_arg_from_env(args, "test", env_var_to_bool)

    return args

def parse_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument("--build-dir")
    parser.add_argument("--build-type")
    parser.add_argument("--clang-tidy", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--cxx-compiler")
    parser.add_argument("--jobs", type=int)
    parser.add_argument("--repo", type=pathlib.Path)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    return vars(args)

def cmake_bool(value):
    return "TRUE" if value else "FALSE"

def log_and_run(cmd, **kwargs):
    cmd = [str(arg) for arg in cmd]
    kwargs = {k: str(v) for k, v in kwargs.items()}
    logging.info(f"Running command {json.dumps(cmd)} with options {json.dumps(kwargs)}")
    return subprocess.run(cmd, **kwargs)

def configure(args):
    args['build_dir'].mkdir(exist_ok=True, parents=True)
    cmake_args = [
        "cmake",
        "-GNinja",
        f"-DCMAKE_BUILD_TYPE={args['build_type']}",
        f"-DSQ_USE_CLANG_TIDY={cmake_bool(args['clang_tidy'])}",
        f"-DSQ_USE_COVERAGE={cmake_bool(args['coverage'])}",
        f"-DCMAKE_CXX_COMPILER={args['cxx_compiler']}",
        args['repo'],
    ]
    log_and_run(cmake_args, cwd=args['build_dir'], check=True)

def build(args):
    log_and_run(["ninja", f"-j{args['jobs']}"], cwd=args['build_dir'], check=True)

def test(args):
    log_and_run(["ninja", "test"], cwd=args['build_dir'], check=True)

def coverage(args):
    gcov = "gcov" if args['cxx_compiler'] == "g++" else "llvm-gcov"
    coveralls_args = [
        "coveralls",
        "--gcov", gcov,
        "--root", args['repo'],
        "--build-root", args['build_dir'],
        "-i", "src/",
        "--exclude", "_deps/",
        "--exclude-pattern", ".*/test/.*",
    ]
    log_and_run(coveralls_args, cwd=args['build_dir'], check=True)

def main():
    args = get_default_args()
    args.update(parse_env())
    args.update(parse_args())

    if not args['build_dir'].is_absolute():
        args['build_dir'] = args['repo'] / args['build_dir']

    logging.basicConfig(level=logging.INFO)
    configure(args)
    build(args)
    if args['test'] or args['coverage']:
        test(args)
    if args['coverage']:
        coverage(args)

main()
