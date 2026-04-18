# GEMINI.md - GitHub Actions Scripts

This project is a collection of utility scripts (Python and Fish shell)
designed for use within GitHub Actions workflows to automate common tasks
like PR creation, repository cloning, and dependency version updates.

## Project Overview

- **Purpose:** Automate GitHub repository management and CI/CD tasks.
- **Main Technologies:**
  - **Python:** 3.12+ (managed and run via `uv`).
  - **Fish Shell:** For specialized shell scripting tasks.
  - **Libraries:** `github-rest-api`, `dulwich`, `requests`.
- **Architecture:** A flat collection of standalone scripts and a `docker/` subdirectory for Docker-specific automation.

## Key Scripts

- `create_pull_request.py`: Creates a pull request between two branches.
- `git_clone_repo.fish`: Clones a repository using SSH, useful for bypassing default GITHUB_TOKEN limitations.
- `docker/update_version_dockerfile.py`: Monitors GitHub releases and updates version strings in Dockerfiles.

## Building and Running

### Prerequisites

- [uv](https://docs.astral.sh/uv/) must be installed.

### Running Python Scripts

The Python scripts use PEP 723 script metadata, allowing them to be run directly with `uv run` without manual environment setup.

```bash
# Example: Create a PR
uv run --script create_pull_request.py \
  --token $GITHUB_TOKEN \
  --head-branch feature-branch \
  --base-branch main

# Example: Update a Dockerfile version
uv run --script docker/update_version_dockerfile.py \
  --token $GITHUB_TOKEN \
  --repo owner/repo \
  --dockerfile path/to/Dockerfile
```

### Running Fish Scripts

```bash
fish git_clone_repo.fish
```

## Development Conventions

- **Python Version:** Use Python 3.12 or newer.
- **Dependency Management:** Add dependencies to the `# /// script` metadata block at the top of Python files.
- **GitHub Interaction:** Prefer using the `github-rest-api` library for consistency.
- **Workflow Integration:** Scripts are often invoked via `curl` and piped to `uv run` in GitHub Actions (see `.github/workflows/create_pr_dev_to_main.yml`).
- **Style:** Follow PEP 8 for Python and use descriptive variable names in Shell scripts.
- **Branch Filtering:** `create_pull_request.py` ignores branches starting with `_`.
