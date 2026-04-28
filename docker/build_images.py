# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "dulwich>=1.1.0",
#     "tenacity>=9.1.4",
# ]
# ///

import argparse
import datetime
from pathlib import Path
import subprocess as sp
import sys
from dulwich.repo import Repo
from dulwich.diff_tree import tree_changes
from tenacity import retry, stop_after_attempt, wait_exponential

DIRS = [
    "docker-base",
    "docker-rust",
    "docker-rust-utils",
    "docker-rust-cicd",
    "docker-python-portable",
    "docker-python",
    "docker-python-nodejs",
    "docker-jupyterlab",
    "docker-jupyterhub",
    "docker-jupyterhub-jdk",
    "docker-jupyterhub-more",
    "docker-vscode-server",
    "docker-jupyterhub-ds",
    # "docker-gitpod",
    # "docker-jupyterhub-cuda",
    # "docker-jupyterhub-pytorch",
    "docker-tensorboard",
    "docker-jupyterhub-kotlin",
    # "docker-jupyterhub-ganymede",
    # "docker-rustpython",
]


def _get_commit(name: bytes) -> bytes:
    """Resolve a commit SHA or branch name to a commit SHA string."""
    repo = Repo(".")
    if name in repo:
        return name
    for prefix in [b"refs/heads/", b"refs/remotes/origin/", b"refs/tags/"]:
        ref = prefix + name
        if ref in repo.refs:
            return repo.refs[ref]
    raise KeyError(f"Cannot resolve commit or branch: {name}")


def changed_files_between(commit1: bytes, commit2: bytes) -> list[Path]:
    """Get a unique list of changed files between 2 commits.

    :param commit1: The first commit ID.
    :param commit2: The second commit ID.
    :return: A unique list of changed files.
    """
    repo = Repo(".")
    c1 = repo[commit1]
    c2 = repo[commit2]
    changes = tree_changes(repo.object_store, c1.tree, c2.tree)
    files = set()
    for change in changes:
        if change.old and change.old.path:
            files.add(change.old.path.decode())
        if change.new and change.new.path:
            files.add(change.new.path.decode())
    return sorted(Path(file).resolve() for file in files)


def has_relevant_changes(commit1: str | bytes, commit2: str | bytes) -> bool:
    if not commit1 or not commit2:
        return True
    if isinstance(commit1, str):
        commit1 = commit1.encode()
    if isinstance(commit2, str):
        commit2 = commit2.encode()
    dirs = [Path(d).resolve() for d in DIRS]
    for p in changed_files_between(commit1, commit2):
        if any(p.is_relative_to(d) for d in dirs):
            return True
    return False


def has_relevant_changes_main_dev() -> bool:
    try:
        c_main = _get_commit(b"main")
        c_dev = _get_commit(b"dev")
    except Exception:
        return True
    return has_relevant_changes(c_main, c_dev)


def _tag_date(tag: str) -> str:
    """Suffix a tag with the current date as a 6-digit string.

    :param tag: A tag of Docker image.
    :return: A new tag.
    """
    return tag + datetime.datetime.now().strftime("_%m%d%H")


@retry(
    stop=stop_after_attempt(3), wait=wait_exponential(multiplier=60, min=60, max=300)
)
def _push_image(image: str):
    sp.run(
        ["docker", "push", image],
        shell=False,
        check=True,
    )


def _build_image(dir_: str, tags: str | list[str]):
    if isinstance(tags, str):
        tags = [tags]
    image = dir_.replace("docker-", "dclong/")
    print(f"\n\nBuilding the Docker image {image}...", flush=True)
    cmd = ["docker", "build", dir_]
    for tag in tags:
        cmd.append("-t")
        cmd.append(f"{image}:{tag}")
    sp.run(cmd, shell=False, check=True)
    for tag in tags:
        _push_image(f"{image}:{tag}")


def build_images(commit1: str, commit2: str):
    if not has_relevant_changes(commit1, commit2):
        print(
            f"Skip building Docker images as there are no relevant changes between {commit1} and {commit2}.\n"
        )
        return
    tags = ["next"]
    if not has_relevant_changes_main_dev():
        tags.append("latest")
    tags.extend([_tag_date(tag) for tag in tags])
    print("Building Docker images using tags:", ", ".join(tags), "\n", flush=True)
    failures = []
    for dir_ in DIRS:
        try:
            _build_image(dir_, tags=tags)
        except Exception as _:
            failures.append(dir_)
    if failures:
        sys.exit(f"\n\nError: failed to build images: {', '.join(failures)}\n")


def test_has_relevant_changes():
    """Test the has_relevant_changes function."""
    # 88c806c -> 36bfa44 includes changes to build_images.py and .github/workflows/
    # These are NOT in the DIRS list.
    c_prev = "88c806c40617773e7d2034c07b0d6c5dc9569e36"
    c_curr = "36bfa44633b3e43bafd602708b0a661038880472"
    print(f"Testing between {c_prev} and {c_curr}...")
    assert not has_relevant_changes(c_prev, c_curr)

    # Verification with relevant changes (docker-base modified in 92d141a)
    c_base_prev = "fad79533497acbf6d84c615a935282e8a6ff2872"
    c_base_curr = "92d141a8cd432581526fa6a11cb8574918d643dc"
    print(f"Testing relevant change between {c_base_prev} and {c_base_curr}...")
    assert has_relevant_changes(c_base_prev, c_base_curr)

    # Verification with empty SHAs (should return True by default)
    print("Testing with empty SHAs...")
    assert has_relevant_changes("", "")


def parse_args():
    """Parse command-line arguments.

    :return: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Build Docker images.")
    parser.add_argument(
        "-c1",
        "--commit1",
        dest="commit1",
        default="",
        help="The first commit ID (empty by default).",
    )
    parser.add_argument(
        "-c2",
        "--commit2",
        dest="commit2",
        default="",
        help="The second commit ID (empty by default).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    build_images(args.commit1, args.commit2)


if __name__ == "__main__":
    main()
