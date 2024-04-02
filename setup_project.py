import argparse
import logging
import subprocess
from pathlib import Path

import requests
import toml
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)

import logging
import subprocess


def setup_pyenv(base_path, python_version):
    # Ensure the specified Python version is installed using pyenv
    try:
        # Set the local Python version for the project
        subprocess.check_output(["pyenv", "local", python_version], cwd=base_path)
        logging.info(
            f"Set up pyenv with Python {python_version} locally for the project"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Error with pyenv setup: {e.output.decode()}")


def set_poetry_environment(base_path):
    try:
        # Ensure this command is correctly obtaining the Python version from pyenv
        pyenv_python_path = subprocess.check_output(
            ["pyenv", "which", "python"], cwd=base_path, text=True
        ).strip()
        subprocess.run(
            ["poetry", "env", "use", pyenv_python_path], cwd=base_path, check=True
        )
        logging.info(f"Poetry environment set to use Python at: {pyenv_python_path}")
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Could not configure Poetry to use the pyenv Python version: {e}"
        )


def create_project_structure(base_path, structure):
    for item in structure:
        if isinstance(item, str):
            # Create a directory for string items
            path = base_path / item
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {path}")
            if "src" in path.parts:
                # Create __init__.py in src and its subdirectories
                (path / "__init__.py").touch()
                logging.info(f"Created __init__.py in {path}")
        elif isinstance(item, dict):
            for folder, nested_items in item.items():
                # Create a directory for each key in dictionary items
                folder_path = base_path / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created directory: {folder_path}")
                if isinstance(nested_items, list):
                    for nested_item in nested_items:
                        if isinstance(nested_item, str):
                            # Create a file if the nested item is a string
                            file_path = folder_path / nested_item
                            file_path.touch()
                            logging.info(f"Created file: {file_path}")
                        elif isinstance(nested_item, dict):
                            # Recursively handle nested directories
                            create_project_structure(folder_path, [nested_item])
                if "src" in folder_path.parts:
                    # Create __init__.py in src and its subdirectories
                    (folder_path / "__init__.py").touch()
                    logging.info(f"Created __init__.py in {folder_path}")


def setup_git(base_path, remote_url=None):
    subprocess.run(["git", "init"], cwd=base_path, check=True)
    if remote_url:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url], cwd=base_path, check=True
        )
        initial_commit_and_push(base_path, remote_url)


def initial_commit_and_push(base_path, remote_url):
    subprocess.run(["git", "add", "."], cwd=base_path, check=True, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=base_path, check=True)
    if remote_url:
        subprocess.run(
            ["git", "push", "-u", "origin", "master"], cwd=base_path, check=True
        )


def create_standard_files(base_path, gitignore_url, pre_commit_config_url, license_url):
    # Combines fetching and creating both .gitignore, .pre-commit-config.yaml and README.md

    def fetch_file(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Failed to fetch file from {url}: {e}")
            return None

    gitignore_content = fetch_file(gitignore_url)
    if gitignore_content:
        (base_path / ".gitignore").write_text(gitignore_content)
        logging.info("Created .gitignore")

    pre_commit_config_content = fetch_file(pre_commit_config_url)
    if pre_commit_config_content:
        pre_commit_config_path = base_path / ".pre-commit-config.yaml"
        pre_commit_config_path.write_text(pre_commit_config_content)
        logging.info("Downloaded and created .pre-commit-config.yaml")
        subprocess.run(["pre-commit", "install"], cwd=base_path, check=True)
        logging.info("Set up pre-commit hooks")

    license_content = fetch_file(license_url)
    if license_content:
        (base_path / "LICENSE").write_text(license_content)
        logging.info("Created LICENSE file")

    # Create README.md as before
    (base_path / "README.md").write_text(f"# Project {base_path.name}\n")


def update_pyproject(base_path, config):
    pyproject_path = base_path / "pyproject.toml"
    pyproject = toml.load(pyproject_path)
    pyproject["tool"]["poetry"]["name"] = config["project_name"]
    pyproject["tool"]["poetry"]["version"] = config.get("version", "0.1.0")
    pyproject["tool"]["poetry"]["readme"] = "README.md"
    pyproject["tool"]["poetry"]["dependencies"]["python"] = "^" + config.get(
        "python_version"
    )
    pyproject["tool"]["poetry"]["authors"] = []
    toml.dump(pyproject, pyproject_path.open("w"))


def create_dockerfile(base_path, python_version):
    dockerfile_content = f"""
    # Use an official Python runtime as a parent image
    FROM python:{python_version}-slim

    # Set the working directory in the container
    WORKDIR /usr/src/app

    # Copy the current directory contents into the container at /usr/src/app
    COPY . /usr/src/app

    # Install any needed packages specified in pyproject.toml
    RUN pip install poetry
    RUN poetry config virtualenvs.create false
    RUN poetry install

    # Make port 80 available to the world outside this container
    EXPOSE 80

    # Define environment variable
    ENV NAME World

    # Run app.py when the container launches
    CMD ["python", "your_script.py"]
    """
    (base_path / "Dockerfile").write_text(dockerfile_content.strip())
    logging.info("Created Dockerfile")


def setup_testing_and_ci_cd(base_path):
    ci_cd_config = """
    name: Python application

    on: [push, pull_request]

    jobs:
    build:
        runs-on: ubuntu-latest
        strategy:
        matrix:
            python-version: [3.6, 3.7, 3.8, 3.9, 3.10]

        steps:
        - uses: actions/checkout@v2
        - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v2
        with:
            python-version: ${{ matrix.python-version }}
        - name: Install dependencies
        run: |
            pip install poetry
            poetry install
        - name: Test with pytest
        run: |
            poetry run pytest
    """
    (base_path / ".github" / "workflows" / "python-app.yml").mkdir(
        parents=True, exist_ok=True
    )
    (base_path / ".github" / "workflows" / "python-app.yml" / "ci-cd.yaml").write_text(
        ci_cd_config.strip()
    )
    logging.info("Created CI/CD configuration")


def main(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    project_name = config["project_name"]
    dependencies = config["dependencies"]
    structure = config.get("structure", [])
    remote_url = config.get("remote_url", None)
    python_version = config.get("python_version", "3.8")
    pre_commit_config_url = config.get(
        "pre_commit_config_url",
        "https://raw.githubusercontent.com/pre-commit/pre-commit-hooks/master/ci/pre-commit-config.yaml",
    )
    gitignore_url = config.get(
        "gitignore_url",
        "https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore",
    )
    license_url = config.get(
        "license_url",
        "https://github.com/git/git-scm.com/blob/main/MIT-LICENSE.txt",
    )

    base_path = Path("..").resolve() / project_name

    base_path.mkdir(parents=True, exist_ok=True)
    create_project_structure(base_path, structure)
    setup_pyenv(base_path, python_version)

    subprocess.run(
        ["poetry", "init", "--no-interaction", "--name", project_name],
        cwd=str(base_path),
        check=True,
    )

    set_poetry_environment(base_path)
    update_pyproject(base_path, config)

    error_log = []  # List to keep track of installation errors

    if dependencies is not None:
        for group, deps in dependencies.items():
            for dep in deps:
                try:
                    dep_command = ["poetry", "add"]

                    # Check if the dependency is for development (-D) or main
                    if group != "main":
                        dep_command.append("-D")

                    # Special handling for torch or torchvision to use the custom source
                    if dep in ["torch", "torchvision"]:
                        dep_command.extend(["--source", "pytorch_cpu", dep])
                    else:
                        dep_command.append(dep)

                    subprocess.run(
                        dep_command,
                        cwd=str(base_path),
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except subprocess.CalledProcessError as e:
                    # Log the error for this dependency
                    error_message = (
                        f"Failed to add dependency '{dep}' due to an error: {e.stderr}"
                    )
                    logging.error(error_message)
                    # Add the error message to the error_log list
                    error_log.append(error_message)

    create_dockerfile(base_path, python_version)

    setup_git(base_path, remote_url)

    create_standard_files(base_path, gitignore_url, pre_commit_config_url, license_url)
    setup_testing_and_ci_cd(base_path)

    if error_log:
        logging.error("There were errors installing some dependencies:")
        for error in error_log:
            logging.error(error)

    logging.info(f"Project {project_name} set up at {base_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Python Project")
    parser.add_argument("config", help="Path to the project configuration YAML file")
    args = parser.parse_args()

    main(args.config)
