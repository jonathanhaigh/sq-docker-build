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
    for env_var in (var.upper(), f"SQ_{var.upper()}", f"INPUT_{var.upper()}"):
        if env_var in os.environ:
            args[var] = typ(os.environ[env_var])

def hide_secrets(key, value):
    if key.upper() in ("COVERALLS_REPO_TOKEN",):
        return "****"
    else:
        return value

def serialize(thing):
    if isinstance(thing, list):
        return json.dumps([str(arg) for arg in thing])
    elif isinstance(thing, dict):
        return {k: hide_secrets(k, str(v)) for k, v in thing.items()}
    else:
        return str(thing)

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
        args['repo'] = pathlib.Path(os.environ['GITHUB_WORKSPACE'])

    get_arg_from_env(args, "build_dir", pathlib.Path)
    get_arg_from_env(args, "build_type", str)
    get_arg_from_env(args, "clang_tidy", env_var_to_bool)
    get_arg_from_env(args, "coverage", env_var_to_bool)
    get_arg_from_env(args, "coveralls_repo_token", str)
    get_arg_from_env(args, "cxx_compiler", str)
    get_arg_from_env(args, "install_prefix", str)
    get_arg_from_env(args, "jobs", int)
    get_arg_from_env(args, "repo", pathlib.Path)
    get_arg_from_env(args, "test", env_var_to_bool)

    return args

def parse_cmdline_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument("--build-dir", type=pathlib.Path)
    parser.add_argument("--build-type")
    parser.add_argument("--clang-tidy", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--coveralls-repo-token")
    parser.add_argument("--cxx-compiler")
    parser.add_argument("--install-prefix", type=pathlib.Path)
    parser.add_argument("--jobs", type=int)
    parser.add_argument("--repo", type=pathlib.Path)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    return vars(args)

def parse_args():
    default_args = get_default_args()
    env_args = parse_env()
    cmdline_args = parse_cmdline_args()
    logging.info(f"default settings: {serialize(default_args)}")
    logging.info(f"environment settings: {serialize(env_args)}")
    logging.info(f"command line settings: {serialize(cmdline_args)}")

    args = { }
    args.update(default_args)
    args.update(env_args)
    args.update(cmdline_args)

    if not args['build_dir'].is_absolute():
        args['build_dir'] = args['repo'] / args['build_dir']

    logging.info(f"aggregated settings: {serialize(args)}")

    return args


def cmake_bool(value):
    return "TRUE" if value else "FALSE"

def log_and_run(args, cmd, **kwargs):
    logging.info(f"Running command {serialize(cmd)} with options {serialize(kwargs)}")
    if "check" not in kwargs:
        kwargs['check'] = True
    if "cwd" not in kwargs:
        kwargs['cwd'] = args['build_dir']
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
    ]

    if 'install_prefix' in args:
        cmake_args.append(f"-DCMAKE_INSTALL_PREFIX={args['install_prefix']}")

    if args['test']:
        cmake_args.append(f"-DSQ_BUILD_TESTS=TRUE")

    cmake_args.append(args['repo'])
    log_and_run(args, cmake_args)

def build(args):
    log_and_run(args, ["ninja", f"-j{args['jobs']}"])

def install(args):
    log_and_run(args, ["ninja", "install"])

def test(args):
    log_and_run(args, ["ninja", "test"])

def coveralls(args):
    # Note: don't use subprocess.run/log_and_run's "env" parameter - we don't
    # want to log the secret coveralls repo token
    os.environ['COVERALLS_REPO_TOKEN'] = args['coveralls_repo_token']

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
    log_and_run(args, coveralls_args)

def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    configure(args)
    build(args)
    install(args)
    exception = None
    try:
        if args['test'] or args['coverage']:
            test(args)
    except subprocess.CalledProcessError as e:
        exception = e

    if 'coveralls_repo_token' in args:
        coveralls(args)

    if exception:
        raise exception

main()
