# Python Project Setup Script

## Overview

This script streamlines the creation of a new Python project. It builds the project structure, initializes a Poetry environment, manages dependencies, sets up a Git repository, prepares a Dockerfile, configures pre-commit hooks, and sets up a CI/CD pipeline using GitHub Actions. The configurations are specified in a YAML file.

## Prerequisites

- **Python** (3.6 or newer)
- **pyenv** for managing Python versions
- **Poetry** for dependency management
- **Git** for version control
- **pre-commit** for managing and maintaining pre-commit hooks
- **Docker** for containerization


## Configuration

Create a `project_config.yaml` file with your project's configurations. Here is an example template:

```yaml
project_name: "my_project"
version: "0.1.0"
python_version: "^3.8"
dependencies:
  main:
    - "tiktoken"
  test:
    - "pytest"
structure:
  - "src":
      - "models":
      - "scripts":
  - "tests"
remote_url: "https://github.com/yourusername/my_project.git"
```

Customize this template according to your project requirements.

## Usage

1. Prepare the YAML Configuration File: Place your project_config.yaml in the same directory as the script or know its path.
2. Run the Script: Navigate to the directory containing the script and execute it with Python, providing the path to your YAML configuration file:

```bash
python setup_project.py project_config.yaml
```

3. Project Structure: The script sets up your project directory with the specified structure, including pyproject.toml for Poetry, a Git repository, a Dockerfile, pre-commit hooks, and CI/CD configuration.
4. Activating the Virtual Environment: Navigate to your project's directory and activate the Poetry-managed virtual environment:

```bash
cd my_project  # Replace with your actual project's name
poetry shell
```

## What the Script Does

- Creates a new project directory with the specified structure.
- Initializes a Poetry project with dependencies.
- Updates the `pyproject.toml` with project details.
- Creates `.gitignore` and `README.md`.
- Initializes a Git repository and sets a remote URL if provided.
- Generates a Dockerfile.
- Sets up pre-commit hooks.
- Configures a CI/CD pipeline using GitHub Actions for automated testing across multiple Python versions.
