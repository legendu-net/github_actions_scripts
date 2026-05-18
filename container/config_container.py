#!/usr/bin/env -S uv run
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "tomli-w",
# ]
# ///

import json
import shutil
import tomllib
import tomli_w
from pathlib import Path
import subprocess as sp


def config_docker(data_root: str = "/mnt/docker"):
    if not shutil.which("docker"):
        print("Docker not found, skipping Docker configuration.")
        return
    Path(data_root).mkdir(parents=True, exist_ok=True)
    sp.run("systemctl stop docker", shell=True, check=True)
    path = Path("/etc/docker/daemon.json")
    settings: dict = {}
    if path.is_file():
        with path.open("r", encoding="utf-8") as fin:
            settings = json.load(fin)
    settings["data-root"] = data_root
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fout:
        json.dump(settings, fout, indent=4)
    print(settings)
    sp.run("systemctl start docker", shell=True, check=True)
    sp.run("docker info", shell=True, check=True)


def config_podman(graphroot: str = "/mnt/podman"):
    if not shutil.which("podman"):
        print("Podman not found, skipping Podman configuration.")
        return
    Path(graphroot).mkdir(parents=True, exist_ok=True)
    path = Path("/etc/containers/storage.conf")
    settings: dict = {}
    if path.is_file():
        with path.open("rb") as fin:
            settings = tomllib.load(fin)
    storage = settings.setdefault("storage", {})
    storage["graphroot"] = graphroot
    storage.setdefault("driver", "overlay")
    storage.setdefault("runroot", "/run/containers/storage")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fout:
        tomli_w.dump(settings, fout)
    print(settings)
    sp.run("podman info", shell=True, check=True)


if __name__ == "__main__":
    config_docker()
    config_podman()
