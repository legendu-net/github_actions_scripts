#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "dulwich>=0.25.1",
#     "github-rest-api>=0.29.0",
#     "requests>=2.33.1",
# ]
# ///
import argparse
import os
from pathlib import Path
import re
import subprocess as sp
from dulwich import porcelain
from github_rest_api import Repository
from github_rest_api.utils import strip_patch_version
from requests.exceptions import HTTPError


def parse_latest_version(repo: str) -> str:
    r = Repository(token="", repo=repo)
    try:
        release = r.get_release_latest()
        version = release["tag_name"]
    except HTTPError as err:
        if err.response is not None and err.response.status_code == 404:
            tags = r._get(r._url_tags, params={"per_page": 1}).json()
            version = tags[0]["name"]
        else:
            raise err
    version = version.replace("v", "")
    print(f"The latest version of {repo} is v{version}.")
    return version


def update_version(
    dockerfile: str | Path, version: str, pattern: str, replace: str
) -> None:
    if dockerfile == "":
        dockerfile = "Dockerfile"
    if isinstance(dockerfile, str):
        dockerfile = Path(dockerfile).resolve()
    match dockerfile.parent.name:
        case "docker-base":
            return _update_version_docker_base(dockerfile=dockerfile, version=version)
        case "docker-jupyterlab":
            return _update_version_docker_jupyterlab(
                dockerfile=dockerfile, version=version
            )
        case "docker-jupyterhub":
            return _update_version_docker_jupyterhub(
                dockerfile=dockerfile, version=version
            )
        case "docker-vscode-server":
            return _update_version_docker_vscode_server(
                dockerfile=dockerfile, version=version
            )
        case _:
            if not pattern:
                raise ValueError("A version pattern must be specified!")
            return _update_version_default(
                dockerfile=dockerfile, version=version, pattern=pattern, replace=replace
            )


def _update_version_default(
    dockerfile: Path, version: str, pattern: str, replace: str
) -> None:
    text = dockerfile.read_text()
    text = re.sub(pattern, replace.format(version=version), text)
    dockerfile.write_text(text)


def _update_version_docker_base(dockerfile: Path, version: str) -> None:
    _update_version_default(
        dockerfile=dockerfile,
        version=version,
        pattern=r"-v v?\d+\.\d+\.\d+",
        replace="-v v{version}",
    )


def _update_version_docker_jupyterlab(dockerfile: Path, version: str) -> None:
    version = strip_patch_version(version)
    _update_version_default(
        dockerfile=dockerfile,
        version=version,
        pattern=r",<\d+\.\d+\.0",
        replace=",<{version}",
    )


def _update_version_docker_jupyterhub(dockerfile: Path, version: str) -> None:
    version = strip_patch_version(version)
    _update_version_default(
        dockerfile=dockerfile,
        version=version,
        pattern=r"jupyterhub<\d+\.\d+\.0",
        replace="jupyterhub<{version}",
    )


def _update_version_docker_vscode_server(dockerfile: Path, version: str) -> None:
    version = strip_patch_version(version)
    _update_version_default(
        dockerfile=dockerfile,
        version=version,
        pattern=r",<\d+\.\d+\.0",
        replace=",<{version}",
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
    except sp.CalledProcessError as err:
        print(err.stdout)
        print(err.stderr)
    except Exception as err:
        raise err
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
        "--dockerfile",
        dest="dockerfile",
        default="",
        help="The Dockerfile to update.",
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
    update_version(
        dockerfile=args.dockerfile,
        version=version,
        pattern=args.pattern,
        replace=args.replace,
    )
    push_changes(repo=args.repo, token=args.token)


if __name__ == "__main__":
    main()
