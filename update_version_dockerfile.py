#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "dulwich>=0.25.1",
#     "github-rest-api>=0.29.0",
# ]
# ///
from pathlib import Path
import os
import re
import subprocess as sp
from github_rest_api import Repository
from github_rest_api.utils import strip_patch_version
import argparse
from dulwich import porcelain

DOCKERFILE = Path.cwd() / "Dockerfile"


def parse_latest_version(repo: str) -> str:
    release = Repository(token="", repo=repo).get_release_latest()
    version = release["tag_name"].replace("v", "")
    print(f"The latest version of {repo} is v{version}.")
    return version


def update_version(version: str, pattern: str, replace: str) -> None:
    match os.getenv("GITHUB_REPOSITORY"):
        case "legendu-net/docker-base":
            return _update_version_docker_base(version=version)
        case "legendu-net/docker-jupyterlab":
            return _update_version_docker_jupyterlab(version=version)
        case "legendu-net/docker-vscode-server":
            return _update_version_docker_vscode_server(version=version)
        case _:
            if not pattern:
                raise ValueError("A version pattern must be specified!")
            return _update_version_default(
                version=version, pattern=pattern, replace=replace
            )


def _update_version_default(version: str, pattern: str, replace: str) -> None:
    text = DOCKERFILE.read_text()
    text = re.sub(pattern, replace.format(version=version), text)
    DOCKERFILE.write_text(text)


def _update_version_docker_base(version: str) -> None:
    _update_version_default(
        version=version, pattern=r"-v v?\d+\.\d+\.\d+", replace="-v v{version}"
    )


def _update_version_docker_jupyterlab(version: str) -> None:
    version = strip_patch_version(version)
    _update_version_default(
        version=version, pattern=r",<\d+\.\d+\.0", replace=",<{version}"
    )


def _update_version_docker_vscode_server(version: str) -> None:
    version = strip_patch_version(version)
    _update_version_default(
        version=version, pattern=r",<\d+\.\d+\.0", replace=",<{version}"
    )


def push_changes(repo: str, token: str):
    if not porcelain.status().unstaged:
        print("No changes!")
        return
    porcelain.add(paths="Dockerfile")
    porcelain.commit(message=f"update version of {repo}")
    try:
        proc = sp.run(
            f"git push https://{token}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git",
            shell=True,
            check=True,
            capture_output=True,
        )
        print(proc.stdout)
    except Exception as err:
        print(err.stdout)
        print(err.stderr)
    return
    porcelain.push(
        repo=".",
        remote_location=f"https://{token}@github.com/{
            os.getenv('GITHUB_REPOSITORY')
        }.git",
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Update the version of icon in Dockerfile."
    )
    parser.add_argument(
        "--token",
        dest="token",
        required=True,
        help="A GitHub token for the repo to be updated.",
    )
    parser.add_argument(
        "--repo",
        dest="repo",
        required=True,
        help="The GitHub repo (in the format of owner/repo) whose release versions are watched.",
    )
    parser.add_argument(
        "--pattern",
        dest="pattern",
        default="",
        help="The version pattern to replace.",
    )
    parser.add_argument(
        "--replace",
        dest="replace",
        default="",
        help="The replacement for the matched version pattern.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    version = parse_latest_version(repo=args.repo)
    update_version(version=version, pattern=args.pattern, replace=args.replace)
    push_changes(repo=args.repo, token=args.token)


if __name__ == "__main__":
    main()
