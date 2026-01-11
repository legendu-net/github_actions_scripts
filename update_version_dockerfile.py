#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "dulwich>=0.25.1",
#     "github-rest-api>=0.26.0",
# ]
# ///
from pathlib import Path
import re
from github_rest_api import Repository
import argparse
from dulwich import porcelain

DOCKERFILE = Path(__file__).parent.parent / "Dockerfile"


def parse_latest_version(token: str, repo: str) -> str:
    repo = Repository(token=token, repo=repo)
    release = repo.get_release_latest()
    version = release["tag_name"].replace("v", "")
    print(f"The latest version of {repo} is v{version}.")
    return version


def update_version(version: str, pattern: str, replace: str) -> None:
    text = DOCKERFILE.read_text()
    text = re.sub(pattern, replace.format(version=version), text)
    DOCKERFILE.write_text(text)


def push_changes(branch: str, repo_watching: str):
    if not porcelain.status().unstaged:
        print("No changes!")
        return
    porcelain.add(paths="Dockerfile")
    porcelain.commit(message=f"update version of {repo_watching}")
    porcelain.push(repo=".")
    print("Changes have been committeed and pushed.")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Update the version of icon in Dockerfile."
    )
    parser.add_argument("--token", dest="token", default="", help="A GitHub token.")
    parser.add_argument(
        "--repo",
        dest="repo",
        required=True,
        help="The GitHub repo (in the format of owner/repo) whose release versions are watched.",
    )
    parser.add_argument(
        "--pattern",
        dest="pattern",
        required=True,
        help="The version pattern to replace.",
    )
    parser.add_argument(
        "--replace",
        dest="replace",
        required=True,
        help="The replacement for the matched version pattern.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    update_version(token=args.token, repo=args.repo)
    push_changes(branch=args.branch)


if __name__ == "__main__":
    main()
