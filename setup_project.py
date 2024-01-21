import yaml
import subprocess
import argparse
import logging
import toml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_project_structure(base_path, structure):
    for item in structure:
        if isinstance(item, str):
            # Create a directory for string items
            path = base_path / item
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {path}")
            if "src" in path.parts:
                # Create __init__.py in src and its subdirectories
                (path / '__init__.py').touch()
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
                    (folder_path / '__init__.py').touch()
                    logging.info(f"Created __init__.py in {folder_path}")

def setup_git(base_path, remote_url=None):
    subprocess.run(["git", "init"], cwd=base_path, check=True)
    if remote_url:
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=base_path, check=True)
        initial_commit_and_push(base_path, remote_url)
        
def initial_commit_and_push(base_path, remote_url):
    subprocess.run(["git", "add", "."], cwd=base_path, check=True, encoding='utf-8')
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=base_path, check=True)
    if remote_url:
        subprocess.run(["git", "push", "-u", "origin", "master"], cwd=base_path, check=True)

def create_standard_files(base_path):
    (base_path / '.gitignore').write_text("# Add files and folders to ignore\n")
    (base_path / 'README.md').write_text(f"# Project {base_path.name}\n")

def update_pyproject(base_path, config):
    pyproject_path = base_path / 'pyproject.toml'
    pyproject = toml.load(pyproject_path)
    pyproject['tool']['poetry']['name'] = config['project_name']
    pyproject['tool']['poetry']['version'] = config.get('version', '0.1.0')
    pyproject['tool']['poetry']['readme'] = "README.md"
    pyproject['tool']['poetry']['dependencies']['python'] = config.get('python_version', '^3.8')
    pyproject['tool']['poetry']['authors'] = []
    toml.dump(pyproject, pyproject_path.open('w'))

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
    (base_path / 'Dockerfile').write_text(dockerfile_content.strip())
    logging.info("Created Dockerfile")
    
def setup_pre_commit(base_path):
    subprocess.run(["pre-commit", "install"], cwd=base_path, check=True)
    pre_commit_config = """
    repos:
    -   repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v3.4.0
        hooks:
        -   id: trailing-whitespace
        -   id: end-of-file-fixer
        -   id: check-yaml
        -   id: check-added-large-files
    """
    (base_path / '.pre-commit-config.yaml').write_text(pre_commit_config.strip())
    logging.info("Set up pre-commit hooks")
    
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
    (base_path / '.github' / 'workflows' / 'python-app.yml').mkdir(parents=True, exist_ok=True)
    (base_path / '.github' / 'workflows' / 'python-app.yml' / 'ci-cd.yaml').write_text(ci_cd_config.strip())
    logging.info("Created CI/CD configuration")


def main(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    project_name = config['project_name']
    dependencies = config['dependencies']
    structure = config.get('structure', [])
    remote_url = config.get('remote_url', None)

    base_path = Path(".").resolve() / project_name

    base_path.mkdir(parents=True, exist_ok=True)
    create_project_structure(base_path, structure)

    subprocess.run(["poetry", "init", "--no-interaction", "-n", "--name", project_name], cwd=str(base_path), check=True)
    
    update_pyproject(base_path, config)

    if dependencies is not None:
        for group, deps in dependencies.items():
            for dep in deps:
                if group == 'main':
                    subprocess.run(["poetry", "add", dep], cwd=str(base_path), check=True)
                else:  # For 'test' and other non-main groups
                    subprocess.run(["poetry", "add", "-D", dep], cwd=str(base_path), check=True)
                
    create_standard_files(base_path)
    create_dockerfile(base_path, config.get('python_version', '3.8'))
    
    setup_git(base_path, remote_url)
    
    setup_pre_commit(base_path)
    setup_testing_and_ci_cd(base_path)
    
    logging.info(f"Project {project_name} set up at {base_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Setup Python Project')
    parser.add_argument('config', help='Path to the project configuration YAML file')
    args = parser.parse_args()

    main(args.config)
