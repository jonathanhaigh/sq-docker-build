#!/usr/bin/env python3

import argparse
import json
import logging
import os
import pathlib
import subprocess

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=pathlib.Path, default=pathlib.Path("build"))
    parser.add_argument("--build-type", default="release")
    parser.add_argument("--clang-tidy", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--cxx-compiler", default="clang++")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path("/work"))
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if not args.build_dir.is_absolute():
        args.build_dir = args.repo / args.build_dir

    return args

def cmake_bool(value):
    return "TRUE" if value else "FALSE"

def log_and_run(cmd, **kwargs):
    cmd = [str(arg) for arg in cmd]
    kwargs = {k: str(v) for k, v in kwargs.items()}
    logging.info(f"Running command {json.dumps(cmd)} with options {json.dumps(kwargs)}")
    return subprocess.run(cmd, **kwargs)

def configure(args):
    args.build_dir.mkdir(exist_ok=True, parents=True)
    cmake_args = [
        "cmake",
        "-GNinja",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DSQ_USE_CLANG_TIDY={cmake_bool(args.clang_tidy)}",
        f"-DSQ_USE_COVERAGE={cmake_bool(args.coverage)}",
        f"-DCMAKE_CXX_COMPILER={args.cxx_compiler}",
        args.repo,
    ]
    log_and_run(cmake_args, cwd=args.build_dir, check=True)

def build(args):
    log_and_run(["ninja", f"-j{args.jobs}"], cwd=args.build_dir, check=True)

def test(args):
    log_and_run(["ninja", "test"], cwd=args.build_dir, check=True)

def coverage(args):
    gcov = "gcov" if args.cxx_compiler == "g++" else "llvm-gcov"
    coveralls_args = [
        "coveralls",
        "--gcov", gcov,
        "--root", args.repo,
        "--build-root", args.build_dir,
        "-i", "src/",
        "--exclude", "_deps/",
        "--exclude-pattern", ".*/test/.*",
    ]
    log_and_run(coveralls_args, cwd=args.build_dir, check=True)

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    configure(args)
    build(args)
    if args.test or args.coverage:
        test(args)
    if args.coverage:
        coverage(args)

main()
